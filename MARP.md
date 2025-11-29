# Marp (Markdown Presentation) Cheatsheet

Marp converts Markdown files into presentation slides. It uses standard Markdown syntax extended with specific directives for slide formatting.

## 1. Basics

### Slide Separation
Use `---` to separate slides.

```markdown
# Slide 1

---

# Slide 2
```

### Directives
Directives control the theme, size, and page numbering. They can be global (applied to the whole deck) or local (applied to the current slide).

**Global Directives** (typically at the top of the file):
```markdown
---
marp: true
theme: default
paginate: true
size: 16:9
---
```

**Common Global Directives:**
- `marp: true`: **REQUIRED** to enable Marp.
- `theme`: `default`, `gaia`, or `uncover`.
- `size`: `16:9` (default) or `4:3`.
- `paginate`: `true` to show page numbers.
- `backgroundColor`: Sets default background color (e.g., `#fff`).
- `color`: Sets default text color.

**Local Directives** (use HTML comments inside a slide):
```markdown
<!-- _class: lead -->
<!-- _paginate: false -->
```
- Prefix with `_` to apply ONLY to the current slide.
- Without `_`, it applies to the current slide AND all following slides.

## 2. Images & Backgrounds

### Standard Images
Standard Markdown syntax works, but you can add sizing options in the alt text.

```markdown
![width:200px](image.jpg)
![height:30cm](image.jpg)
![w:32 h:32](image.jpg)
```

### Background Images
Use `bg` in the alt text to make an image a background.

```markdown
![bg](background.jpg)
```

**Scaling Options:**
- `![bg cover](img.jpg)`: Fill slide (default).
- `![bg contain](img.jpg)`: Fit to slide.
- `![bg 80%](img.jpg)`: Scale to percentage.

**Split Backgrounds:**
You can split the slide between an image and text.
```markdown
![bg left:33%](image.jpg)

# Content on the right
This text appears on the remaining 67% of the slide.
```
- `left`: Image on left.
- `right`: Image on right.
- `vertical`: Stack vertical (complex).

### Image Filters
Apply CSS filters directly in the alt text.
```markdown
![bg brightness:0.8 sepia:0.5](image.jpg)
```
- `blur:10px`
- `brightness:1.5`
- `grayscale:1`
- `opacity:0.5`
- `drop-shadow:0,5px,10px,rgba(0,0,0,0.4)`

## 3. Layout & Styling

### Themes
- **default**: Standard white background, simple text.
- **gaia**: Colorful, closer to Keynote/PowerPoint styles.
- **uncover**: Centered text, minimal, good for simple messages.

### Class
Use the `class` directive to apply preset styles.
```markdown
<!-- _class: lead -->
```
- `lead`: Centers content in the middle (great for title slides).
- `invert`: Inverts colors (dark background, light text).

### Scoped Styling
You can inject standard CSS using the `<style>` tag, but keep it simple.

```markdown
<style>
section {
  font-size: 30px;
}
</style>
```

### Header & Footer
```markdown
---
header: 'Confidential'
footer: 'Page %PAGE%'
---
```

## 4. Code Blocks
Standard Markdown code blocks are supported and highlighted.

```python
def hello():
    print("Hello world")
```

## 5. Speaker Notes
Add comments that won't appear on the slide but will show in presenter mode.

```markdown
<!--
Here are some notes for the presenter.
Don't forget to mention X and Y.
-->
```

