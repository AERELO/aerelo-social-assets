"""Offline setup checks. No network, no real key, no paid calls.   Run: python3 -m unittest discover -s tools/social/tests -v"""
import base64
import contextlib
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import imagegen as ig  # noqa: E402
import layouts as lay  # noqa: E402
import social as soc  # noqa: E402
from PIL import Image  # noqa: E402

REPO = ig.REPO


def png_b64(size=(64, 96), color="#223") -> str:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


class FakeClient:
    """Stands in for openai.OpenAI. Counts calls, records kwargs, can be told to fail."""
    def __init__(self, fail=None):
        self.calls, self.fail = [], fail
        self.images = self
        self.with_raw_response = self

    def generate(self, **kw):
        self.calls.append(kw)
        if self.fail:
            raise self.fail
        usage = mock.Mock()
        usage.model_dump.return_value = {"input_tokens": 100, "output_tokens": 1000,
                                         "input_tokens_details": {"text_tokens": 100, "image_tokens": 0}}
        resp = mock.Mock(data=[mock.Mock(b64_json=png_b64())], usage=usage)
        return mock.Mock(headers={"x-request-id": f"req_test_{len(self.calls)}"}, parse=lambda: resp)


def base_manifest(slug):
    return {
        "slug": slug, "topic": "test", "format": "portrait", "brand": {"name": "AERELO", "theme": "night"},
        "image_defaults": {"model": ig.DEFAULT_MODEL, "quality": "high", "size": "1024x1536"},
        "assets": [{"id": "a1", "prompt": "abstract one"}, {"id": "a2", "prompt": "abstract two"}],
        "slides": [
            {"layout": "cover", "headline": "Hello\nworld", "artwork": {"asset": "a1", "mode": "panel"}},
            {"layout": "content", "title": "Point", "lead": "Short lead.", "artwork": {"asset": "a2", "mode": "full"}},
            {"layout": "close", "headline": "Done."},
        ],
    }


class Setup(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.budget = {"auto_approve": True, "max_images_per_post": 6, "max_images_per_day": 20, "max_regens_per_asset": 2}
        for patcher in (mock.patch.object(soc, "SPEND_LOG", self.tmp / "_spend" / "log.jsonl"),
                        mock.patch.object(soc, "load_budget", lambda: dict(self.budget))):
            patcher.start()
            self.addCleanup(patcher.stop)

    def post(self, slug="t-post", mutate=None):
        d = self.tmp / slug
        d.mkdir()
        m = base_manifest(slug)
        if mutate:
            mutate(m)
        (d / "manifest.json").write_text(json.dumps(m))
        return d

    # ---- credentials ------------------------------------------------------------------
    def test_env_file_ignored_example_tracked(self):
        ign = lambda f: subprocess.run(["git", "-C", str(REPO), "check-ignore", "-q", f]).returncode == 0  # noqa: E731
        self.assertTrue(ign(".env.images"))
        self.assertFalse(ign(".env.images.example"))
        self.assertIn("sk-REPLACE", (REPO / ".env.images.example").read_text())

    def test_missing_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ig.MissingKey) as cm:
                ig.load_api_key(self.tmp / "nope.env")
        self.assertNotIn("sk-", str(cm.exception).replace("sk-REPLACE", ""))

    def test_placeholder_key_rejected(self):
        f = self.tmp / ".env.images"
        f.write_text("OPENAI_API_KEY=sk-REPLACE_WITH_YOUR_KEY\n")
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ig.MissingKey):
                ig.load_api_key(f)

    def test_reads_only_the_key_and_redacts(self):
        f = self.tmp / ".env.images"
        f.write_text("OTHER_SECRET=zzz\nOPENAI_API_KEY='sk-test1234567890abcd'\n")
        with mock.patch.dict(os.environ, {}, clear=True):
            key, src = ig.load_api_key(f)
        self.assertEqual(key, "sk-test1234567890abcd")
        self.assertNotIn("1234567890", ig.redact(f"bad key {key}"))

    def test_refuses_unignored_env_file_inside_repo(self):
        f = REPO / "tools/social/tests/_leaky.env"
        f.write_text("OPENAI_API_KEY=sk-test1234567890abcd\n")
        self.addCleanup(lambda: f.exists() and f.unlink())
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ig.ImageGenError) as cm:
                ig.load_api_key(f)
        self.assertIn("not git-ignored", str(cm.exception))

    # ---- request shape ----------------------------------------------------------------
    def test_request_shape(self):
        kw = ig.build_request("p", ig.DEFAULT_MODEL, "high", "1024x1536")
        self.assertNotIn("response_format", kw)
        self.assertNotIn("complexity", kw)
        self.assertEqual((kw["n"], kw["output_format"], kw["stream"], kw["quality"], kw["model"]),
                         (1, "png", False, "high", "gpt-image-2.6-sunburst"))
        self.assertEqual(ig.build_request("p", "m", "low", "1024x1024", "medium")["complexity"], "medium")

    def test_param_validation(self):
        self.assertEqual(ig.validate_params(ig.DEFAULT_MODEL, "high", "1024x1536"), [])
        with self.assertRaises(ig.ImageGenError):
            ig.validate_params(ig.DEFAULT_MODEL, "ultra", "1024x1536")
        with self.assertRaises(ig.ImageGenError):
            ig.validate_params(ig.DEFAULT_MODEL, "high", "1080x1350")           # custom, no opt-in
        self.assertTrue(ig.validate_params(ig.DEFAULT_MODEL, "high", "1072x1344", None, True))
        with self.assertRaises(ig.ImageGenError):
            ig.validate_params(ig.DEFAULT_MODEL, "high", "1080x1350", None, True)  # not divisible by 16
        self.assertTrue(ig.validate_params("other-model", "high", "1024x1024"))      # warns, never substitutes

    def test_client_has_no_sdk_retries(self):
        c = ig.make_client("sk-test1234567890abcd", 5)
        self.assertEqual(c.max_retries, 0)

    # ---- generation, overwrite protection, ledger ------------------------------------
    def test_generate_writes_file_and_never_overwrites(self):
        out, fc = self.tmp / "o" / "x.png", FakeClient()
        rec = ig.generate_image("p", out, client=fc)
        self.assertTrue(out.is_file())
        self.assertEqual(rec["request_id"], "req_test_1")
        self.assertNotIn("b64", json.dumps(rec))
        self.assertIn("ESTIMATE", rec["cost_estimate"]["basis"])
        self.assertNotIn("response_format", fc.calls[0])
        before = out.read_bytes()
        with self.assertRaises(ig.ImageGenError):
            ig.generate_image("p", out, client=fc)
        self.assertEqual(len(fc.calls), 1)                                         # refused BEFORE calling the API
        self.assertEqual(out.read_bytes(), before)

    # ---- manifest validation ------------------------------------------------------------
    def test_sample_manifest_valid(self):
        m = json.loads((REPO / "content/sample-carousel/manifest.json").read_text())
        E, _ = soc.validate_manifest(m, REPO / "content/sample-carousel")
        self.assertEqual(E, [])

    def test_manifest_rejections(self):
        def errs(mut):
            d = self.post(slug="t-" + str(len(list(self.tmp.iterdir()))), mutate=mut)
            return soc.validate_manifest(json.loads((d / "manifest.json").read_text()), d)[0]
        self.assertTrue(any("Studios" in e for e in errs(lambda m: m["slides"][0].update(headline="AERELO Studios"))))
        self.assertTrue(any("prices" in e for e in errs(lambda m: m["slides"][1].update(lead="From US$195 only"))))
        self.assertTrue(any("not defined" in e for e in errs(lambda m: m["slides"][0]["artwork"].update(asset="nope"))))
        self.assertTrue(any("layout" in e for e in errs(lambda m: m["slides"][0].update(layout="weird"))))
        self.assertTrue(any("plain .png" in e for e in errs(lambda m: m["assets"][0].update(output="../x.png"))))
        self.assertTrue(any("duplicate" in e for e in errs(lambda m: m["assets"][1].update(id="a1"))))
        self.assertTrue(any("exactly one" in e for e in errs(lambda m: m["assets"][0].update(existing="x.png"))))
        self.assertTrue(any("size" in e for e in errs(lambda m: m["assets"][0].update(size="1080x1350"))))

    # ---- batch behaviour: cache, stale, regen, failure, render-only -------------------
    def run_cli(self, *argv, client=None):
        buf = io.StringIO()
        client = client or FakeClient()
        with mock.patch.object(ig, "make_client", lambda *a, **k: client), \
             mock.patch.object(ig, "load_api_key", lambda *a, **k: ("sk-fake0000000000", "test")), \
             contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = soc.main(list(argv))
        return code, buf.getvalue(), client

    def test_cache_reuse_stale_and_regen(self):
        d = self.post()
        code, _, c = self.run_cli("generate", str(d), "--dry")        # --dry -> preview only
        self.assertEqual((code, len(c.calls)), (0, 0))
        code, _, c = self.run_cli("generate", str(d))                 # auto_approve: runs inside budget, no --yes needed
        self.assertEqual((code, len(c.calls)), (0, 2))
        led = json.loads((d / "assets/ledger.json").read_text())
        self.assertEqual(led["assets"]["a1"]["history"][0]["request_id"], "req_test_1")
        self.assertTrue((d / "assets/originals/a1.png").is_file())
        code, out, c = self.run_cli("generate", str(d))      # rerun: everything cached
        self.assertEqual(len(c.calls), 0)
        self.assertIn("Nothing to generate", out)
        m = json.loads((d / "manifest.json").read_text())             # edit a prompt -> stale, NOT auto-paid
        m["assets"][0]["prompt"] = "changed"
        (d / "manifest.json").write_text(json.dumps(m))
        code, out, c = self.run_cli("generate", str(d))
        self.assertEqual(len(c.calls), 0)
        self.assertIn("stale", out)
        v1 = (d / "assets/originals/a1.png").read_bytes()
        code, out, c = self.run_cli("regen", str(d), "a1")   # explicit regen -> new version, old kept
        self.assertEqual((code, len(c.calls)), (0, 1))
        self.assertTrue((d / "assets/originals/a1-v2.png").is_file())
        self.assertEqual((d / "assets/originals/a1.png").read_bytes(), v1)
        code, out, c = self.run_cli("status", str(d))
        self.assertIn("cached", out)

    def test_failure_stops_batch_and_ambiguous_blocks_rerun(self):
        import openai
        d = self.post()
        err = openai.PermissionDeniedError("no access", response=mock.Mock(status_code=403, headers={}), body=None)
        code, out, c = self.run_cli("generate", str(d), client=FakeClient(fail=err))
        self.assertEqual((code, len(c.calls)), (1, 1))                # stopped after first failure
        self.assertIn("No other model was substituted", out)
        d2 = self.post(slug="t-post2")
        to = openai.APITimeoutError(request=mock.Mock())
        code, out, c = self.run_cli("generate", str(d2), client=FakeClient(fail=to))
        self.assertEqual((code, len(c.calls)), (1, 1))
        code, out, c = self.run_cli("generate", str(d2))     # blocked until user confirms
        self.assertEqual((code, len(c.calls)), (2, 0))
        self.assertIn("--retry-pending", out)

    def test_render_only_makes_no_api_calls_and_checks_output(self):
        d = self.post()
        code, out, c = self.run_cli("render", str(d))                 # no art, no placeholders -> refuse
        self.assertEqual(code, 2)
        code, out, c = self.run_cli("render", str(d), "--placeholders")
        self.assertEqual((code, len(c.calls)), (0, 0), out)
        for k in (1, 2, 3):
            with Image.open(d / f"exports/slide-0{k}.png") as im:
                self.assertEqual(im.size, (1080, 1350))
        self.assertTrue((d / "contact-sheet.png").is_file())
        self.assertTrue((d / "source/slide-01.html").is_file())
        # real (fake-PNG) artwork present -> render uses it, still without any API call
        self.run_cli("generate", str(d))
        code, out, c2 = self.run_cli("render", str(d), "--only", "2")      # official logo files absent -> refuse
        self.assertEqual((code, len(c2.calls)), (2, 0))
        self.assertIn("brand/logo", out)
        code, out, c2 = self.run_cli("render", str(d), "--only", "2", "--placeholders")
        self.assertEqual((code, len(c2.calls)), (0, 0), out)
        self.assertNotIn("PLACEHOLDER ARTWORK", out)                       # real (cached) art was used
        self.assertIn("PLACEHOLDER LOGO", out)

    def test_story_and_square_formats_render(self):
        for fmt, size in (("story", (1080, 1920)), ("square", (1080, 1080))):
            d = self.post(slug=f"t-{fmt}", mutate=lambda m, f=fmt: m.update(format=f))
            code, out, _ = self.run_cli("render", str(d), "--placeholders")
            self.assertEqual(code, 0, out)
            with Image.open(d / "exports/slide-01.png") as im:
                self.assertEqual(im.size, size)

    # ---- budget -------------------------------------------------------------------------
    def test_budget_caps_and_modes(self):
        d = self.post()
        self.budget["max_images_per_post"] = 1                         # plan needs 2 -> refused before any call
        code, out, c = self.run_cli("generate", str(d))
        self.assertEqual((code, len(c.calls)), (2, 0))
        self.assertIn("max_images_per_post", out)
        code, out, c = self.run_cli("generate", str(d), "--override-budget")
        self.assertEqual((code, len(c.calls)), (0, 2))
        self.assertEqual(soc.requests_today(), 2)
        self.budget.update(max_images_per_post=6, max_images_per_day=2)  # daily cap already used up
        d2 = self.post(slug="t-day")
        code, out, c = self.run_cli("generate", str(d2))
        self.assertEqual((code, len(c.calls)), (2, 0))
        self.assertIn("daily cap", out)

    def test_auto_approve_off_requires_yes(self):
        d = self.post()
        self.budget["auto_approve"] = False
        code, out, c = self.run_cli("generate", str(d))
        self.assertEqual((code, len(c.calls)), (0, 0))
        self.assertIn("PREVIEW ONLY", out)
        code, out, c = self.run_cli("generate", str(d), "--yes")
        self.assertEqual(len(c.calls), 2)

    def test_regen_cap_and_review_sheet(self):
        d = self.post()
        self.run_cli("generate", str(d))
        self.budget["max_regens_per_asset"] = 1
        self.assertEqual(self.run_cli("regen", str(d), "a1")[2].calls.__len__(), 1)        # first redo ok
        code, out, c = self.run_cli("regen", str(d), "a1")                                  # second redo blocked
        self.assertEqual((code, len(c.calls)), (2, 0))
        self.assertIn("regenerated", out)
        code, out, _ = self.run_cli("review", str(d))
        self.assertEqual(code, 0)
        self.assertTrue((d / "assets/review-sheet.png").is_file())

    def test_shared_art_direction_appended_and_changes_cache_key(self):
        d = self.post()
        m = json.loads((d / "manifest.json").read_text())
        full = soc.asset_prompt(m, m["assets"][0], d)
        self.assertIn("abstract one", full)
        self.assertIn("near-black", full)                                  # from brand/art-direction-prompt.txt
        m["image_defaults"]["prompt_suffix"] = ""
        self.assertEqual(soc.asset_prompt(m, m["assets"][0], d), "abstract one")

    # ---- visual regression guard against the existing generator -------------------------
    def test_portrait_geometry_matches_existing_generator(self):
        t = lay.TH["night"]
        for n in (1, 4, 6):
            for i in range(n):
                self.assertEqual(lay.ring_svg(i, n, t, 1080, 1350), lay.GEN.ringsvg(i, n, t))
        self.assertEqual(lay.topbar(t, "Label", 1, 6), lay.GEN.topbar(t, "Label", 1, 6))
        lay.GEN.B = Path("/X")
        self.assertEqual(lay.foot(t, "Swipe →", "file:///X/logo/aerelo-mark-small-light.svg"), lay.GEN.foot(t, "Swipe →"))


if __name__ == "__main__":
    unittest.main()
