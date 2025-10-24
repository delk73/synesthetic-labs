

```bash
python -m labs.cli generate \
  "make a square compositional harmony asset" \
  --engine azure \
  --schema-version 0.7.3
```



```bash
export LABS_LOG_LEVEL=DEBUG
python -m labs.cli generate "debug run" --engine azure --schema-version 0.7.3
```


```bash
# 1. Generate a new test asset
python -m labs.cli generate "a simple test asset with one circle" > /tmp/labs_gen.json

# 2. Run critique against MCP in relaxed mode
LABS_FAIL_FAST=0 python -m labs.cli critique /tmp/labs_gen.json
```