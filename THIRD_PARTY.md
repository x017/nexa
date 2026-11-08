# Third party software

`nexa-ui` (`nexa`) is a Python port of [CUI](https://github.com/yappologistic/CUI) (MIT License) and embeds the following permissive open-source works. Their licenses apply to those parts and are bundled in source and wheel distributions.

| Component | Where | License |
|---|---|---|
| CUI | `csrc/` (`https://github.com/yappologistic/CUI`) | MIT License |
| Inter (Rasmus Andersson) | Embedded in `csrc/src/cui_font_data.c` | SIL Open Font License 1.1, see `csrc/third_party/licenses/LICENSE-Inter.txt` |
| Geist and Geist Mono (Vercel) | Embedded in `csrc/src/cui_font_data.c` | SIL Open Font License 1.1, see `csrc/third_party/licenses/LICENSE-Geist.txt` |
| Lucide icons | Embedded in `csrc/src/cui_font_data.c`; `csrc/include/cui/cui_icons.h` | ISC, see `csrc/third_party/licenses/LICENSE-Lucide.txt` |
| Unicode 17.0.0 data (Unicode, Inc.) | Generated `csrc/src/cui_bidi_data.h` and `csrc/src/cui_joining.h` | Unicode License V3, see `csrc/third_party/licenses/LICENSE-Unicode.txt` |
| stb_truetype, stb_image, stb_image_write, stb_rect_pack (Sean Barrett) | `csrc/third_party/` | Public domain (or MIT) |

The fonts are subsets of the originals (Latin, Latin-1, Latin Extended-A and common symbols). Under the OFL the subsets keep their original names only as embedded data; they are not distributed as separate font products.
