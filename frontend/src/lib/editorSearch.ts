import type { Editor } from '@tiptap/react'

export function findNextInEditor(
  editor: Editor,
  query: string,
  fromIndex = 0,
): number {
  if (!query) return -1
  const text = editor.getText()
  const index = text.indexOf(query, fromIndex)
  if (index < 0) return -1

  const from = textPosToDocPos(editor, index)
  const to = textPosToDocPos(editor, index + query.length)
  if (from < 0 || to < 0) return index
  editor.chain().focus().setTextSelection({ from, to }).scrollIntoView().run()
  return index
}

export function replaceSelectionInEditor(
  editor: Editor,
  replacement: string,
): void {
  const { from, to } = editor.state.selection
  if (from === to) return
  editor.chain().focus().insertContentAt({ from, to }, replacement).run()
}

function textPosToDocPos(editor: Editor, textIndex: number): number {
  let seen = 0
  let result = -1
  editor.state.doc.descendants((node, pos) => {
    if (result >= 0 || !node.isText || !node.text) return
    const next = seen + node.text.length
    if (textIndex <= next) {
      result = pos + (textIndex - seen)
      return false
    }
    seen = next
  })
  return result >= 0 ? result : editor.state.doc.content.size
}
