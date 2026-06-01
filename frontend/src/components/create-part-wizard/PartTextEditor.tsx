import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { useCallback, useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { findNextInEditor, replaceSelectionInEditor } from '@/lib/editorSearch'

interface PartTextEditorProps {
  content: string
  onChange: (text: string) => void
}

export function PartTextEditor({ content, onChange }: PartTextEditorProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [replaceQuery, setReplaceQuery] = useState('')
  const [searchFrom, setSearchFrom] = useState(0)

  const editor = useEditor({
    extensions: [StarterKit],
    content: plainTextToHtml(content),
    editorProps: {
      attributes: {
        dir: 'rtl',
        lang: 'fa',
        class:
          'min-h-[320px] max-h-[60vh] overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-base leading-relaxed focus:outline-none',
      },
    },
    onUpdate: ({ editor: ed }) => {
      onChange(ed.getText())
    },
  })

  useEffect(() => {
    if (!editor) return
    const current = editor.getText()
    if (content !== current) {
      editor.commands.setContent(plainTextToHtml(content), { emitUpdate: false })
    }
  }, [content, editor])

  const handleFindNext = useCallback(() => {
    if (!editor || !searchQuery) return
    const index = findNextInEditor(editor, searchQuery, searchFrom)
    if (index < 0) {
      setSearchFrom(0)
      findNextInEditor(editor, searchQuery, 0)
      return
    }
    setSearchFrom(index + searchQuery.length)
  }, [editor, searchFrom, searchQuery])

  const handleReplace = useCallback(() => {
    if (!editor) return
    replaceSelectionInEditor(editor, replaceQuery)
    onChange(editor.getText())
  }, [editor, onChange, replaceQuery])

  if (!editor) {
    return <div className="h-80 animate-pulse rounded-lg bg-[var(--color-muted)]" />
  }

  return (
    <div className="space-y-3" data-testid="part-text-editor">
      <div className="flex flex-wrap items-end gap-2 border-b border-[var(--color-border)] pb-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
        >
          Undo
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
        >
          Redo
        </Button>
        <div className="flex flex-1 flex-wrap items-end gap-2">
          <div className="grid gap-1">
            <Label htmlFor="editor-search" className="text-xs">
              Search
            </Label>
            <Input
              id="editor-search"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setSearchFrom(0)
              }}
              className="h-8 w-36"
              dir="auto"
            />
          </div>
          <Button type="button" variant="outline" size="sm" onClick={handleFindNext}>
            Find
          </Button>
          <div className="grid gap-1">
            <Label htmlFor="editor-replace" className="text-xs">
              Replace
            </Label>
            <Input
              id="editor-replace"
              value={replaceQuery}
              onChange={(e) => setReplaceQuery(e.target.value)}
              className="h-8 w-36"
              dir="auto"
            />
          </div>
          <Button type="button" variant="outline" size="sm" onClick={handleReplace}>
            Replace
          </Button>
        </div>
      </div>
      <EditorContent editor={editor} />
    </div>
  )
}

function plainTextToHtml(text: string): string {
  if (!text) return '<p></p>'
  return text
    .split('\n')
    .map((line) => `<p dir="rtl">${escapeHtml(line)}</p>`)
    .join('')
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}
