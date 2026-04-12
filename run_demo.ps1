$proc = Start-Process python -ArgumentList "-m", "flashback_ops" -PassThru
Start-Sleep -Seconds 3
try {
  python scripts/live_demo_sequence.py
}
finally {
  Stop-Process -Id $proc.Id -Force
}
