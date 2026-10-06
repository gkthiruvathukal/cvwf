-- Pandoc Lua filter: turns the rendered /cv/ HTML into clean Word structure.
-- The page encodes meaning in Tailwind classes (font-medium, italic, flex rows,
-- grid stats); pandoc ignores those, so we map the ones the CV actually uses
-- to real Word constructs. If cv.astro/components change which classes carry
-- meaning, update the mappings here (see README "Word version").

local function has(el, cls)
  for _, c in ipairs(el.classes) do
    if c == cls then return true end
  end
  return false
end

local function has_any(el, list)
  for _, cls in ipairs(list) do
    if has(el, cls) then return true end
  end
  return false
end

local function is_bold(el) return has_any(el, { "font-semibold", "font-bold", "font-medium" }) end

-- Wrap every inline of a block's content in Strong/Emph.
local function wrap_blocks(blocks, ctor)
  return blocks:walk({
    Plain = function(p) return pandoc.Plain({ ctor(p.content) }) end,
    Para = function(p) return pandoc.Para({ ctor(p.content) }) end,
  })
end

-- Drop navigation, inline SVG icons and anything marked no-print.
local function RawInline(el) if el.format:match("html") then return {} end end
local function RawBlock(el) if el.format:match("html") then return {} end end
local function Image() return {} end  -- inline SVG icons arrive as images

local function Div(el)
  if has(el, "no-print") then return {} end

  -- Page header block (role, address, contact rows, version badge): the page
  -- centers it in print, so give it the centered "CV Header" paragraph style
  -- defined in templates/reference.docx. Children are still processed below.
  if has(el, "print:text-center") then
    el.attributes["custom-style"] = "CV Header"
    return el
  end

  -- Date | detail rows (EntryRow / LineItem): two children -> borderless 2-col table.
  if has(el, "flex") and has(el, "gap-4") and #el.content == 2 then
    local left, right = el.content[1], el.content[2]
    if left.t == "Div" and right.t == "Div" then
      return pandoc.utils.from_simple_table(pandoc.SimpleTable(
        {}, { pandoc.AlignDefault, pandoc.AlignDefault }, { 0.2, 0.8 }, {},
        { { left.content, right.content } }))
    end
  end
  -- LineItem without a date: single flex-1 child -> just its content.
  if has(el, "flex") and has(el, "gap-4") and #el.content == 1 and el.content[1].t == "Div" then
    return el.content[1].content
  end

  -- Impact Summary stat tiles: one row, N columns.
  if has(el, "grid") then
    local cells, widths, aligns = {}, {}, {}
    for _, tile in ipairs(el.content) do
      if tile.t == "Div" then
        table.insert(cells, tile.content)
        table.insert(widths, 0)
        table.insert(aligns, pandoc.AlignLeft)
      end
    end
    if #cells > 0 then
      return pandoc.utils.from_simple_table(pandoc.SimpleTable({}, aligns, widths, {}, { cells }))
    end
  end

  -- Publication entries (authors / title / venue+year lines): one tight
  -- paragraph with line breaks instead of one paragraph per line, so 200+
  -- entries don't balloon the document.
  if has(el, "avoid-break") and has(el, "py-2.5") then
    local out = pandoc.List()
    for _, line in ipairs(el.content) do
      if line.t == "Div" then
        local inl = pandoc.List()
        for _, b in ipairs(line.content) do
          if b.t == "Plain" or b.t == "Para" then inl:extend(b.content) end
        end
        if #inl > 0 then
          if is_bold(line) then inl = pandoc.List({ pandoc.Strong(inl) })
          elseif has(line, "italic") then inl = pandoc.List({ pandoc.Emph(inl) }) end
          if #out > 0 then out:insert(pandoc.LineBreak()) end
          out:extend(inl)
        end
      end
    end
    if #out > 0 then return pandoc.Para(out) end
  end

  -- Whole-line emphasis (title lines, big stat numbers, venue lines).
  if is_bold(el) or has(el, "text-xl") then
    return pandoc.Div(wrap_blocks(el.content, pandoc.Strong))
  end
  if has(el, "italic") then
    return pandoc.Div(wrap_blocks(el.content, pandoc.Emph))
  end

  -- Contact rows: join items with " | " and drop the decorative "|" spans.
  if has(el, "flex-wrap") then
    local out, first = pandoc.List(), true
    local inlines = pandoc.List()
    for _, b in ipairs(el.content) do
      if b.t == "Plain" or b.t == "Para" then inlines:extend(b.content) end
    end
    for _, il in ipairs(inlines) do
      local skip = il.t == "RawInline" or (il.t == "Span" and has(il, "text-slate-300"))
      if not skip and il.t ~= "Space" and il.t ~= "SoftBreak" then
        if not first then out:insert(pandoc.Str(" | ")) end
        -- Strip the nested decorative "|" span that precedes the text of an item.
        local item = il:walk({ Span = function(sp) if has(sp, "text-slate-300") then return {} end end })
        if item.t == "Span" then
          local c = pandoc.List(item.content)
          while #c > 0 and (c[1].t == "Space" or c[1].t == "SoftBreak") do c:remove(1) end
          out:extend(c)
        else
          out:insert(item)
        end
        first = false
      end
    end
    return pandoc.Para(out)
  end
  -- anything else: leave as is so traversal continues; pass 2 unwraps it.
end

local function Span(el)
  -- Version/date badge: "[tag] v0.5" + "Oct 5, 2026" -> "v0.5 · Oct 5, 2026".
  if has(el, "bg-slate-500") then
    local c = pandoc.List(el.content)
    c:insert(pandoc.Str(" · "))
    return c
  end
  if is_bold(el) then return pandoc.Strong(el.content) end
  if has(el, "italic") then return pandoc.Emph(el.content) end
  return el.content
end

-- Heading levels: the page h1 is the name, supplied as the Word Title via
-- `-M title=...` (scripts/generate-docx.mjs), so drop it; h2/h3 become Heading 1/2.
local function Header(el)
  if el.level == 1 then return {} end
  el.level = el.level - 1
  return el
end

-- Site-relative links (e.g. /publications/) -> absolute so they work in Word.
local function Link(el)
  if el.target:sub(1, 1) == "/" then
    el.target = "https://cv.gkt.sh" .. el.target
  end
  return el
end

-- Pass 2 (runs bottom-up over the whole document): unwrap leftover container
-- Divs, and convert styled/plain Spans.
local function UnwrapDiv(el)
  if el.attributes["custom-style"] then return nil end
  return el.content
end

-- Pass 3: each date row was emitted as its own one-row table; merge runs of
-- adjacent tables with the same column layout into a single table per section.
local function same_cols(a, b)
  if #a.colspecs ~= #b.colspecs then return false end
  for i, spec in ipairs(a.colspecs) do
    if spec[2] ~= b.colspecs[i][2] then return false end
  end
  return true
end

local function MergeTables(blocks)
  local out = pandoc.List()
  for _, b in ipairs(blocks) do
    local last = out[#out]
    if b.t == "Table" and last and last.t == "Table" and same_cols(last, b)
        and #last.head.rows == 0 and #b.head.rows == 0 then
      for _, body in ipairs(b.bodies) do
        for _, row in ipairs(body.body) do last.bodies[1].body:insert(row) end
      end
    else
      out:insert(b)
    end
  end
  return out
end

-- Pass 1 is topdown so a Div can inspect its raw Span children (e.g. the "|"
-- separators) before they are unwrapped.
return {
  { traverse = "topdown", Div = Div, Header = Header },
  { Span = Span, Link = Link, Div = UnwrapDiv,
    Image = Image, RawInline = RawInline, RawBlock = RawBlock },
  { Blocks = MergeTables },
}
