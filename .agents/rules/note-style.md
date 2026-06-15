# Note Writing Style Rules

## Attribution Ban (STRICT)
NEVER write: "the lecturer says", "the teacher explains", "the instructor mentions", "this is discussed in the lecture", "the teacher describes", or any similar attribution phrase. Write the content directly as fact.

## Exception
Hindi mnemonics preserved in *italics* with English meaning: *"सहज पके सो मीठा होय"* (Slow and steady wins the race).

## Anti‑Screenshot‑As‑Content
Screenshots supplement; they do NOT replace written content. Never use "as shown in the screenshot" as a substitute for explaining content.

## Mathematical Explanations and Layout Guidelines
- **Math Formatting**: Always output math expressions clearly. LaTeX syntax inside paragraphs (e.g. `\(ax^2 + bx + c = 0\)`) is preferred for the mapping agent. The compilation script will convert this to unicode. Avoid raw, unparsed LaTeX markup in the final docx.
- **Step-by-Step Layout**: Algebraic manipulations or multi-step explanations must NOT be written in a single block paragraph. They must be formatted with each step on a new line or sentence. For example:
  1. First, evaluate the signs using the Golden Rule.
  2. Next, split the constant term.
  3. Divide by the leading coefficient.
- **Golden Rule Shortcut**: Prioritize checking root signs from equation coefficients before performing any splits. In comparison questions, check if signs are opposite (e.g., all positive roots for one vs all negative roots for the other). If they are, state that no root solving is needed: "Don't even need to solve for roots."
- **Prime Factorization**: For large constant terms, show the step-by-step prime factors ladder and combinations that sum to the middle term.
- **Leading Coefficients (a > 1)**: Explain the product of coefficients `a \times c`, finding factors, and division by the leading coefficient `a` explicitly.
- **Middle Term Square Roots**: Explain the shortcut step-by-step: divide constant `c` by radicand `k`, split `c/k` to sum to `b`, then attach `\sqrt{k}` back.
- **Original Equations**: Always present the original equation forms as written on the board (e.g., fractional equations like `50/x^2 - 15/x + 1 = 0` or decimals like `0.25x^2...`) first, then show the scaled integer equations (e.g., `x^2 - 15x + 50 = 0` or `x^2 + 14x + 45 = 0`).
- **Homework Questions (HW Que)**: Label homework/practice questions explicitly as "Homework Questions (HW Que): Try:" and do not mix them with lecture examples. Do not hallucinate or invent extra questions unless they are explicitly in the source material.
