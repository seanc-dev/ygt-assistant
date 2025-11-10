import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { useEffect, useCallback, useRef } from "react";
import { workroomApi } from "../../lib/workroomApi";
import { Button } from "@ygt-assistant/ui/primitives/Button";
import {
  TextHeader124Regular,
  TextHeader224Regular,
  TextBulletList24Regular,
  TextNumberListLtr24Regular,
  Code24Regular,
  TextQuote24Regular,
} from "@fluentui/react-icons";

interface TaskDocProps {
  taskId: string;
  initialContent?: any;
  onContentChange?: (contentJSON: any) => void;
}

export function TaskDoc({
  taskId,
  initialContent,
  onContentChange,
}: TaskDocProps) {
  // Debounced save function using useRef to persist timeout across renders
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const debouncedSave = useCallback(
    (json: any) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(async () => {
        try {
          await workroomApi.updateTaskDoc(taskId, json);
        } catch (err) {
          console.error("Failed to save task doc:", err);
        }
      }, 1000);
    },
    [taskId]
  );

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2],
        },
      }),
      Placeholder.configure({
        placeholder: "Start writing...",
      }),
    ],
    content: initialContent || {
      type: "doc",
      content: [],
    },
    immediatelyRender: false,
    onUpdate: ({ editor }) => {
      const json = editor.getJSON();
      onContentChange?.(json);
      // Debounce save
      debouncedSave(json);
    },
  });

  useEffect(() => {
    if (editor && initialContent) {
      editor.commands.setContent(initialContent);
    }
  }, [editor, initialContent]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  if (!editor) {
    return <div className="p-4">Loading editor...</div>;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-1 p-2 border-b border-slate-200">
        <Button
          variant="ghost"
          size="sm"
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 1 }).run()
          }
          className={
            editor.isActive("heading", { level: 1 }) ? "bg-slate-100" : ""
          }
        >
          <TextHeader124Regular className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 2 }).run()
          }
          className={
            editor.isActive("heading", { level: 2 }) ? "bg-slate-100" : ""
          }
        >
          <TextHeader224Regular className="w-4 h-4" />
        </Button>
        <div className="w-px h-6 bg-slate-200 mx-1" />
        <Button
          variant="ghost"
          size="sm"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={editor.isActive("bulletList") ? "bg-slate-100" : ""}
        >
          <TextBulletList24Regular className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={editor.isActive("orderedList") ? "bg-slate-100" : ""}
        >
          <TextNumberListLtr24Regular className="w-4 h-4" />
        </Button>
        <div className="w-px h-6 bg-slate-200 mx-1" />
        <Button
          variant="ghost"
          size="sm"
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          className={editor.isActive("codeBlock") ? "bg-slate-100" : ""}
        >
          <Code24Regular className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          className={editor.isActive("blockquote") ? "bg-slate-100" : ""}
        >
          <TextQuote24Regular className="w-4 h-4" />
        </Button>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-y-auto p-4">
        <EditorContent
          editor={editor}
          className="prose prose-sm max-w-none focus:outline-none"
        />
      </div>
    </div>
  );
}
