import pytest
from training.evaluators import WebEvaluator, BackendEvaluator, DatabaseEvaluator


@pytest.mark.asyncio
async def test_web_evaluator_good_output():
    evaluator = WebEvaluator()
    output = """<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width">
<style>body{color:red;}</style>
</head>
<body><script>alert('hi');</script></body>
</html>"""
    score, msg = await evaluator.evaluate(output, None, {})
    assert score > 0.8
    assert "Good job" in msg or "Score: " in msg


@pytest.mark.asyncio
async def test_web_evaluator_bad_output():
    evaluator = WebEvaluator()
    output = "<div>Hello</div>"
    score, msg = await evaluator.evaluate(output, None, {})
    assert score < 0.5
    assert "Missing <html>" in msg or "Missing" in msg


@pytest.mark.asyncio
async def test_backend_evaluator_good_output():
    evaluator = BackendEvaluator()
    output = """from fastapi import FastAPI
app = FastAPI()
@app.get("/")
def read_root():
    return {"hello": "world"}
"""
    score, msg = await evaluator.evaluate(output, None, {})
    assert score > 0.9
    assert "Good job" in msg or "Score: " in msg


@pytest.mark.asyncio
async def test_database_evaluator_good_output():
    evaluator = DatabaseEvaluator()
    output = """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    FOREIGN KEY (group_id) REFERENCES groups(id)
);"""
    score, msg = await evaluator.evaluate(output, None, {})
    assert score > 0.8
    assert "Good job" in msg or "Score: " in msg
