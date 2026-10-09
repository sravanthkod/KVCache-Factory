Method: SNAPKV, Benchmark: RULER

Budget = 1024
Uniform -> 85.35; 85.67
Winner -> 91.10; 91.46
Random -> 87.32; 87.06
Best BO -> 93.22; 93.79 -> better than Winner config

Budget = 1536 
Uniform - > 88.66; 88.62 
Winner -> 98.39; 98.35
Random -> 96.69; 96.86
Best BO -> 98.39; 98.35 -> Same as Winner config

Budget = 2048
Uniform -> 92.41; 92.93
Winner -> 98.88; 98.91
Random -> 98.38; 98.35
Best BO -> 98.50; 98.12 -> worse than winner config

RULER Constrained NAS — Final Results (SnapKV, Llama-3-8B)

┌────────┬─────────┬──────────┬──────────┬──────────┬─────────────┬──────────────────────────┐
│ Budget │ Uniform │ Winner   │  Best    │ Best BO  │ Winner vs   │       Best config        │
│        │         │  shape   │  random  │          │   Uniform   │                          │
├────────┼─────────┼──────────┼──────────┼──────────┼─────────────┼──────────────────────────┤
│ 1024   │ 85.67   │ 91.46    │ 87.06    │ 93.79    │ +5.79       │ BO (+2.33 over winner)   │
├────────┼─────────┼──────────┼──────────┼──────────┼─────────────┼──────────────────────────┤
│ 1536   │ 88.62   │ 98.35    │ 96.86    │ 98.35    │ +9.73       │ Winner (BO converged to  │
│        │         │          │          │ (tied)   │             │ same config)             │
├────────┼─────────┼──────────┼──────────┼──────────┼─────────────┼──────────────────────────┤
│ 2048   │ 92.93   │ 98.91    │ 98.35    │ 98.12    │ +5.98       │ Winner (BO's own best    │
│        │         │          │          │          │             │ was actually worse)      │
└────────┴─────────┴──────────┴──────────┴──────────┴─────────────┴──────────────────────────┘