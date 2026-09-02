from generator import (
    GameGenerationError,
    _parse_combined_response,
    clean_code,
    has_risky_canvas_api,
    is_code_complete,
    pick_template,
)
from templates import COLLECTOR, RUNNER, SHOOTER


class TestTemplates:
    def test_runner_template_valid(self):
        assert is_code_complete(RUNNER) is True
        assert not has_risky_canvas_api(RUNNER)
        assert "requestAnimationFrame" in RUNNER

    def test_collector_template_valid(self):
        assert is_code_complete(COLLECTOR) is True
        assert not has_risky_canvas_api(COLLECTOR)
        assert "requestAnimationFrame" in COLLECTOR

    def test_shooter_template_valid(self):
        assert is_code_complete(SHOOTER) is True
        assert not has_risky_canvas_api(SHOOTER)
        assert "requestAnimationFrame" in SHOOTER

    def test_pick_template_shooter(self):
        assert pick_template("spaceship shoots lasers at aliens") == "shooter"
        assert pick_template("a tank blasting enemies") == "shooter"
        assert pick_template("defend the castle") == "shooter"

    def test_pick_template_runner(self):
        assert pick_template("a robot run and jump over obstacles") == "runner"
        assert pick_template("speedy forest parkour racing") == "runner"

    def test_pick_template_collector(self):
        assert pick_template("a cat collecting candy and gems") == "collector"
        assert pick_template("catch falling fruit") == "collector"

    def test_pick_template_none(self):
        assert pick_template("a wizard fights a dragon with spells") is None

    def test_enhanced_blurb_drops_leading_article(self):
        from generator import _enhanced_blurb

        blurbs = [_enhanced_blurb("a cute cat run jump", "runner")]
        assert not any("A a cute" in b for b in blurbs)
        assert "A cute cat run jump game" in blurbs[0]


class TestCleanCode:
    def test_strips_markdown_fences(self):
        input_text = "```html\n<p>hello</p>\n```"
        assert clean_code(input_text) == "<p>hello</p>"

    def test_strips_whitespace(self):
        assert clean_code("  <html></html>  ") == "<html></html>"

    def test_removes_partial_fences(self):
        input_text = "```js\nconst x = 1;\n```"
        assert clean_code(input_text) == "const x = 1;"

    def test_plain_html_unchanged(self):
        html = "<!DOCTYPE html><html><body>test</body></html>"
        assert clean_code(html) == html


class TestHasRiskyCanvasApi:
    def test_unguarded_roundrect_detected(self):
        assert has_risky_canvas_api("<script>ctx.roundRect(10, 20, 30, 40, 5);</script>") is True

    def test_guarded_roundrect_ok(self):
        assert (
            has_risky_canvas_api(
                "<script>if (ctx.roundRect) { ctx.roundRect(10, 20, 30, 40, 5); }</script>"
            )
            is False
        )

    def test_safe_apis_ok(self):
        assert has_risky_canvas_api("<script>ctx.fillRect(1, 2, 3, 4);</script>") is False


class TestIsCodeComplete:
    def test_valid_complete_html(self):
        code = (
            "<!DOCTYPE html><html><head></head><body>"
            "<canvas id='game' width='800' height='600'></canvas>"
            "<script>function loop() { requestAnimationFrame(loop); } loop();</script>"
            "</body></html>"
        )
        assert is_code_complete(code) is True

    def test_missing_canvas(self):
        code = (
            "<!DOCTYPE html><html><head></head><body>"
            "<script>function loop() { requestAnimationFrame(loop); } loop();</script>"
            "</body></html>"
        )
        assert is_code_complete(code) is False

    def test_missing_closing_html(self):
        code = (
            "<!DOCTYPE html><html><head></head><body>"
            "<canvas id='game' width='800' height='600'></canvas>"
            "<script>function loop() { requestAnimationFrame(loop); } loop();</script>"
            "</body>"
        )
        assert is_code_complete(code) is False

    def test_empty_string(self):
        assert is_code_complete("") is False

    def test_no_requestanimationframe(self):
        code = (
            "<!DOCTYPE html><html><head></head><body>"
            "<canvas id='game' width='800' height='600'></canvas>"
            "<script>function loop() { } loop();</script>"
            "</body></html>"
        )
        assert is_code_complete(code) is False


class TestParseCombinedResponse:
    def test_proper_markers(self):
        raw = "===ENHANCED PROMPT===\nA cool game\n===GAME CODE===\n<!DOCTYPE html><html></html>"
        enhanced, code = _parse_combined_response(raw, "fallback")
        assert enhanced == "A cool game"
        assert "<!DOCTYPE html>" in code

    def test_fallback_to_html_start(self):
        raw = "Some preamble text <!DOCTYPE html><html></html>"
        enhanced, code = _parse_combined_response(raw, "my game")
        assert "<!DOCTYPE html>" in code
        assert enhanced == "Some preamble text"

    def test_last_resort_all_code(self):
        raw = "<!DOCTYPE html><html></html>"
        enhanced, code = _parse_combined_response(raw, "test game")
        assert "test game" in enhanced
        assert "<!DOCTYPE html>" in code


class TestGameGenerationError:
    def test_is_exception(self):
        assert issubclass(GameGenerationError, Exception)

    def test_can_be_raised_and_caught(self):
        try:
            raise GameGenerationError("test")
        except GameGenerationError as e:
            assert str(e) == "test"
