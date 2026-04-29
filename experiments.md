# Experiments

## Baseline
The first baseline predicted `true` only when the normalized current study description exactly matched the prior study description. This was simple and fast, but it missed many clinically useful priors with different wording, for example `MRI BRAIN STROKE LIMITED WITHOUT CONTRAST` compared with `CT HEAD WITHOUT CNTRST`.

## Final approach
The final endpoint uses a deterministic scoring model. For every current/prior pair, it extracts modality, body region, clinical keywords, lexical overlap, and study-date difference. A prior is marked relevant when the score passes a threshold. The strongest signal is same body region plus same or related modality. Recency and clinical overlap provide smaller boosts.

## What worked
Same body region was the most important feature. Modality matching improved precision. A special rule for stroke/head imaging improved examples where a CT head prior should still be useful for a current MRI brain stroke exam.

## What failed
Exact matching alone was too strict. Pure text similarity was too broad and sometimes matched unrelated exams that shared generic words such as contrast or limited. External LLM calls were avoided because the evaluator can send many cases in one request and has a strict timeout.

## Next improvements
I would tune the threshold on the public labeled split, expand the medical synonym dictionary, add exam-family-specific thresholds, and train a lightweight text classifier using the public split. I would also cache repeated current/prior description pairs and log per-request counts to debug evaluator calls.
