# Copilot Instructions for open-llms

## Overview
This repository maintains a curated list of open-source Large Language Models (LLMs) licensed for commercial use. The main content is in [README.md](README.md), organized as markdown tables.

## Table Formats
Use these exact headers for each section:

- **General LLMs**: | Language Model | Release Date | Checkpoints | Paper/Blog | Params (B) | Context Length | Licence | Try it |
- **Code LLMs**: | Language Model | Release Date | Checkpoints | Paper/Blog | Params (B) | Context Length | Licence | Try it |
- **Pre-training Datasets**: | Name | Release Date | Paper/Blog | Dataset | Tokens (T) | License |
- **Instruction-tuning Datasets**: | Name | Release Date | Paper/Blog | Dataset | Samples (K) | License |
- **Alignment-tuning Datasets**: | Name | Release Date | Paper/Blog | Dataset | Samples (K) | License |

## Adding a New Model
1. Verify the model has a commercial-friendly license (Apache 2.0, MIT, etc.).
2. Research and collect: Release Date (YYYY/MM), Checkpoints (Hugging Face links), Paper/Blog, Params (B), Context Length, Licence, Try it link.
3. Insert in the appropriate table, maintaining alphabetical or chronological order.
4. Use format: | Model | Date | [Checkpoints](url) | [Paper](url) | Params | [Length](config) | License | [Try](url) |

Example:
| T5 | 2019/10 | [T5 & Flan-T5](https://github.com/google-research/t5x/blob/main/docs/models.md#flan-t5-checkpoints) | [Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer](https://github.com/google-research/text-to-text-transfer-transformer#released-model-checkpoints) | 0.06 - 11 | [512](https://discuss.huggingface.co/t/does-t5-truncate-input-longer-than-512-internally/3602) | Apache 2.0 | [T5-Large](https://github.com/slai-labs/get-beam/tree/main/examples/t5) |

## Research Workflow
1. Search recent releases on Hugging Face, GitHub, or arXiv for new open LLMs.
2. Check model page for license compatibility (avoid custom licenses with restrictions).
3. Extract params and context length from config.json or model card.
4. Find official paper/blog and functional demo links.
5. Cross-verify dates and metadata for accuracy.

## Verification
- Check Hugging Face model pages for accuracy.
- Ensure "Try it" links are functional demos.
- Update evals links if new leaderboards emerge.

## Updating Existing Models
- When a model releases new checkpoints, papers, or demos, update the corresponding columns.
- Preserve chronological order within tables (newest at bottom).

## Removing Models
- Remove entries if licenses become non-commercial or models are deprecated/unavailable.
- Document removals in commit messages for traceability.

## Datasets and Evals
- Datasets: Include tokens in trillions (T), samples in thousands (K), and link to dataset pages.
- Evals: Maintain current leaderboard links; add emerging ones like new HELM updates.

## License Considerations
- Apache 2.0: Allows commercial use, distribution, modification without royalties.
- MIT: Permits any use, including commercial, with minimal attribution.
- CC BY-SA-4.0: Commercial ok, but derivatives must use same license.
- OpenRAIL-M v1: Flexible sharing, but review use restrictions in license text.
- BSD-3-Clause: Unlimited redistribution, keep copyright notices.

## Important Notes
- Only include models with verified commercial licenses (e.g., Apache 2.0, MIT).
- Repo licensed under [LICENSE](LICENSE); contributions must comply.
- Disclaimer: This list is informational; consult legal experts for commercial use.

## Contributions
- Follow the table structure exactly.
- Add to appropriate section (general, code, datasets).
- Update the "Improvements" checklist in README if relevant.
