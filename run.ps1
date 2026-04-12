if (-not $env:FLASHBACK_MEMORY_BACKEND) { $env:FLASHBACK_MEMORY_BACKEND = "local" }
if (-not $env:FLASHBACK_DATA_FILE) { $env:FLASHBACK_DATA_FILE = "data/memory.json" }
python -m flashback_ops
