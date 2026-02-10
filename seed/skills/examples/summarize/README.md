# Skill: Summarize

## What It Does
Summarizes text input to a specified length.

## When to Use
When the agent needs to condense long text (articles, logs, conversations)
into a brief summary for memory or responses.

## Usage
```bash
echo "long text here" | ./run.sh [max_words]
```

## Arguments
- `max_words` (optional): Maximum words in summary. Default: 100.

## Output
Summarized text on stdout.
