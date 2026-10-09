# 🎨🪚 ArtSaw Essential Tools for ComfyUI

**The easiest way to batch your ComfyUI queue with folders, prompts, and images.**

ArtSaw Essential Tools removes repetitive manual file selection from your workflows. Point a node at a folder, choose an index, and pull the matching prompt or image directly into ComfyUI.

Built for dataset workflows, image sequences, prompt libraries, and repeatable batch queues.

## Included Nodes

### Load Prompt from Folder by Index | 🎨🪚 ArtSaw

Loads a text prompt from a folder by its sorted index.

Use it to:

- Cycle through a library of prompts.
- Match a prompt to an image or dataset index.
- Build queue workflows without manually pasting text.
- Use natural sorting, so `prompt_2.txt` appears before `prompt_10.txt`.

### Load Image from Folder by Index | 🎨🪚 ArtSaw

Loads one image from a folder by its sorted index.

Use it to:

- Load the matching source image for a queue item.
- Pair images with prompt files that share the same ordering.
- Step through image sequences without changing filenames manually.
- Read files from nested folders when needed.

### Load Image Batch from Folder | 🎨🪚 ArtSaw

Loads a sorted group of same-size images as one ComfyUI batch.

Use it to:

- Process entire image folders in one workflow.
- Prepare image sequences for batch generation or transformation.
- Limit the number of loaded images when testing a workflow.
- Keep image order stable and predictable.

### Inspect Folder Path | 🎨🪚 ArtSaw

Reads a folder path and shows its name, parent directory, and immediate subfolders.

Use it to:

- Navigate large asset libraries.
- Confirm folder paths inside a workflow.
- Inspect project and dataset structure without leaving ComfyUI.
- Build reusable workflows that work across multiple folders.

## Best For

- Batch queues
- Prompt libraries
- Image datasets
- Image sequences
- Dataset pairing
- Folder navigation
- Repeatable ComfyUI workflows
