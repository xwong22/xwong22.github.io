---
title: "A Writing Guide for This Blog"
description: "Footnotes that live in the margin, math that renders properly, and everything else a technical post needs."
date: 2026-09-29
tags: [meta]
# description: shown under the title, in the blog list, and in search/social previews
# math: false          # (optional) skip loading KaTeX on posts without equations
---

This post is a living demo of what the blog supports. Open the source file in `_posts/` next to the rendered page to see how each feature is written, and delete this post once you no longer need it.

## Footnotes become sidenotes

Write ordinary Markdown footnotes and they appear in the right margin, next to the line that cites them.[^tufte] This is the layout popularised by Edward Tufte's books, and it keeps citations readable without sending you to the bottom of the page. On a phone, tap the number to open the note inline.

Footnotes can hold citations, like the original transformer paper,[^attention] as well as longer asides with several paragraphs, code or math.[^long] You can give them descriptive labels such as `[^attention]`; they are numbered automatically in order of appearance.

Sometimes you want a remark without a number.{% include marginnote.html text="This is a *margin note*: unnumbered, and handy for small asides or figure credits." %} Use the `marginnote` include for that.

## Mathematics

Inline math is written between double dollar signs, so $$\nabla_\theta \log p_\theta(x)$$ sits comfortably in a sentence. A display equation goes in its own paragraph:

$$
\mathrm{Attention}(Q, K, V) = \mathrm{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right) V
$$

Aligned, multi-line derivations work too:

$$
\begin{aligned}
\mathcal{L}_{\text{ELBO}}(\theta, \phi)
  &= \mathbb{E}_{q_\phi(z \mid x)}\big[\log p_\theta(x \mid z)\big]
     - \mathrm{KL}\big(q_\phi(z \mid x) \,\|\, p(z)\big) \\
  &\le \log p_\theta(x).
\end{aligned}
$$

Math also works inside footnotes.[^mathnote]

## Code

```python
import torch

def scaled_dot_product(q, k, v):
    scores = q @ k.transpose(-2, -1) / q.size(-1) ** 0.5
    return scores.softmax(dim=-1) @ v
```

## Tables, quotes and figures

| Model     | Params | Accuracy |
|-----------|-------:|---------:|
| Baseline  |  125M  |   71.2   |
| Ours      |  125M  | **74.8** |

> The purpose of computing is insight, not numbers.
> — Richard Hamming

<figure>
  <img src="{{ '/assets/img/avatar.svg' | relative_url }}" alt="Placeholder figure" width="220">
  <figcaption>Figure 1. Put images in <code>assets/img/</code> and caption them like this.</figcaption>
</figure>

[^tufte]: See Edward R. Tufte, *Beautiful Evidence* (Graphics Press, 2006), and the [Tufte CSS](https://edwardtufte.github.io/tufte-css/) project.

[^attention]: A. Vaswani et al., "Attention Is All You Need," *NeurIPS* 2017. [arXiv:1706.03762](https://arxiv.org/abs/1706.03762).

[^long]: A footnote can span several paragraphs.

    Indent continuation paragraphs by four spaces, as in this one.

[^mathnote]: For example, $$\mathrm{KL}(q \,\|\, p) \ge 0$$ with equality iff $$q = p$$.
