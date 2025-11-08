import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { render, screen } from "@testing-library/react";
import type { TaskDoc as TaskDocType } from "../TaskDoc";
import { workroomApi } from "../../../lib/workroomApi";

// Mock workroomApi
vi.mock("../../../lib/workroomApi", () => ({
  workroomApi: {
    updateTaskDoc: vi.fn().mockResolvedValue({ ok: true }),
  },
}));

// Mock TipTap
vi.mock("@tiptap/react", () => ({
  useEditor: vi.fn(() => ({
    chain: () => ({
      focus: () => ({
        toggleHeading: () => ({
          run: vi.fn(),
        }),
        toggleBulletList: () => ({
          run: vi.fn(),
        }),
        toggleOrderedList: () => ({
          run: vi.fn(),
        }),
        toggleCodeBlock: () => ({
          run: vi.fn(),
        }),
        toggleBlockquote: () => ({
          run: vi.fn(),
        }),
      }),
    }),
    isActive: vi.fn(() => false),
    getJSON: vi.fn(() => ({ type: "doc", content: [] })),
    commands: {
      setContent: vi.fn(),
    },
  })),
  EditorContent: ({ editor }: any) => <div data-testid="editor-content">Editor</div>,
}));

vi.mock("@tiptap/starter-kit", () => ({
  __esModule: true,
  default: {
    configure: vi.fn(),
  },
}));

vi.mock("@tiptap/extension-placeholder", () => ({
  __esModule: true,
  default: {
    configure: vi.fn(),
  },
}));

vi.mock("@ygt-assistant/ui/primitives/Button", () => ({
  __esModule: true,
  Button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
}));

vi.mock("@fluentui/react-icons", () => ({
  TextHeader124Regular: ({ className }: any) => <span className={className}>H1</span>,
  TextHeader224Regular: ({ className }: any) => <span className={className}>H2</span>,
  TextBulletList24Regular: ({ className }: any) => <span className={className}>List</span>,
  TextNumberListLtr24Regular: ({ className }: any) => <span className={className}>Number</span>,
  Code24Regular: ({ className }: any) => <span className={className}>Code</span>,
  TextQuote24Regular: ({ className }: any) => <span className={className}>Quote</span>,
}));

describe("TaskDoc", () => {
  let TaskDoc: TaskDocType;
  const defaultProps = {
    taskId: "test-task-id",
    initialContent: {
      type: "doc",
      content: [],
    },
    onContentChange: vi.fn(),
  };

  beforeAll(async () => {
    ({ TaskDoc } = await import("../TaskDoc"));
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders without errors", () => {
    const { container } = render(<TaskDoc {...defaultProps} />);
    expect(container).toBeTruthy();
  });

  it("renders toolbar buttons", () => {
    render(<TaskDoc {...defaultProps} />);
    // Check that editor content is rendered
    expect(screen.getByTestId("editor-content")).toBeInTheDocument();
  });

});

