from ollamarama_irc.tools import load_schema, execute_tool


def test_load_schema_list():
    schema = load_schema()
    assert isinstance(schema, list)
    assert any((t.get("function") or {}).get("name") == "calculate_expression" for t in schema)


def test_execute_builtin_math():
    out = execute_tool("calculate_expression", {"expression": "1+2*3"})
    assert "result" in out

