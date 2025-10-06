declare module "@headlessui/react" {
  import type * as React from "react";

  interface DialogProps {
    open: boolean;
    onClose(value: boolean): void;
    as?: React.ElementType;
    children?: React.ReactNode;
  }

  type DialogPanelProps = React.ComponentPropsWithoutRef<"div">;
  type DialogTitleProps = React.ComponentPropsWithoutRef<"h2">;

  const DialogComponent: React.FC<DialogProps> & {
    Panel: React.FC<DialogPanelProps>;
    Title: React.FC<DialogTitleProps>;
  };

  interface TransitionProps {
    show?: boolean;
    appear?: boolean;
    enter?: string;
    enterFrom?: string;
    enterTo?: string;
    leave?: string;
    leaveFrom?: string;
    leaveTo?: string;
    as?: React.ElementType;
    children?: React.ReactNode;
  }

  const TransitionComponent: React.FC<TransitionProps> & {
    Child: React.FC<TransitionProps>;
  };

  export { DialogComponent as Dialog, TransitionComponent as Transition };
}

declare module "@dnd-kit/core" {
  import type { ReactNode } from "react";

  export interface SensorDescriptor {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    sensor: any;
    options: unknown;
  }

  export interface DndContextProps {
    children?: ReactNode;
    sensors?: SensorDescriptor[];
    onDragStart?: (event: unknown) => void;
    onDragEnd?: (event: unknown) => void;
  }

  export const DndContext: React.FC<DndContextProps>;
  export const PointerSensor: unknown;
  export const KeyboardSensor: unknown;
  export function useSensor(sensor: unknown, options?: unknown): SensorDescriptor;
  export function useSensors(...sensors: SensorDescriptor[]): SensorDescriptor[];
  export interface UseDroppableArguments {
    id: string;
    data?: unknown;
  }
  export interface UseDroppableReturnValue {
    isOver: boolean;
    setNodeRef: (element: HTMLElement | null) => void;
  }
  export function useDroppable(args: UseDroppableArguments): UseDroppableReturnValue;
  export interface UseDraggableArguments {
    id: string;
    data?: unknown;
  }
  export interface UseDraggableReturnValue {
    setNodeRef: (element: HTMLElement | null) => void;
    attributes: Record<string, unknown>;
    listeners: Record<string, unknown>;
    transform: { x: number; y: number } | null;
    transition?: string;
  }
  export function useDraggable(args: UseDraggableArguments): UseDraggableReturnValue;
  export interface DragOverlayProps {
    children?: ReactNode;
  }
  export const DragOverlay: React.FC<DragOverlayProps>;
}

declare module "@dnd-kit/sortable" {
  import type * as React from "react";

  export interface SortableContextProps {
    items: Array<{ id: string } | string>;
    strategy?: unknown;
    children?: React.ReactNode;
  }
  export const SortableContext: React.FC<SortableContextProps>;
  export const arrayMove: <T>(items: T[], from: number, to: number) => T[];
  export const rectSortingStrategy: unknown;
  export function useSortable(options: { id: string; data?: unknown }): {
    setNodeRef: (element: HTMLElement | null) => void;
    attributes: Record<string, unknown>;
    listeners: Record<string, unknown>;
    transform: { x: number; y: number } | null;
    transition: string | undefined;
  };
}

declare module "@dnd-kit/utilities" {
  export type Transform = { x: number; y: number; scaleX?: number; scaleY?: number } | null | undefined;
  export const CSS: {
    Transform: {
      toString(transform?: Transform): string;
    };
  };
}

declare module "@tanstack/react-query" {
  export class QueryClient {
    getQueryData<T>(queryKey: unknown): T | undefined;
    setQueryData<T>(queryKey: unknown, updater: T | ((oldData: T | undefined) => T)): void;
    setQueriesData<T>(
      filters: unknown,
      updater: T | ((oldData: T | undefined) => T | undefined),
    ): void;
    invalidateQueries(queryKey?: unknown): Promise<void> | void;
  }

  export interface QueryClientProviderProps {
    client: QueryClient;
    children?: React.ReactNode;
  }

  export const QueryClientProvider: React.FC<QueryClientProviderProps>;
  export function useQuery<TQueryFnData = unknown, TError = unknown, TData = TQueryFnData>(options: {
    queryKey: unknown;
    queryFn: () => Promise<TQueryFnData> | TQueryFnData;
    enabled?: boolean;
  }): {
    data: TData | undefined;
    isLoading: boolean;
    isPending: boolean;
    error: TError | null;
  };
  export function useMutation<TData = unknown, TError = unknown, TVariables = void>(options: {
    mutationFn: (variables: TVariables) => Promise<TData> | TData;
    onSuccess?: (data: TData) => void;
  }): {
    mutate: (variables: TVariables) => void;
    isLoading: boolean;
    isPending: boolean;
    error: TError | null;
    mutateAsync: (variables: TVariables) => Promise<TData>;
  };
  export function useQueryClient(): QueryClient;
}

declare module "@tanstack/react-query-devtools" {
  export const ReactQueryDevtools: React.FC<{ initialIsOpen?: boolean }>;
}

declare module "@coachflow/ui" {}

declare module "clsx" {
  export default function clsx(...inputs: Array<string | number | Record<string, boolean> | undefined | null | false>): string;
}

declare module "date-fns" {
  export function format(date: Date | number, formatStr: string): string;
}

declare module "next-auth" {
  export interface Session {
    user?: { name?: string | null; email?: string | null } | null;
  }
  export interface NextAuthOptions {
    providers: unknown[];
    session?: unknown;
    callbacks?: Record<string, (...args: unknown[]) => unknown>;
  }
}

declare module "next-auth/react" {
  import type { Session } from "next-auth";
  export function useSession(): { data: Session | null; status: "loading" | "authenticated" | "unauthenticated" };
  export function signIn(
    provider?: string,
    options?: Record<string, unknown>,
  ): Promise<{ error?: string } | null>;
  export function signOut(options?: Record<string, unknown>): Promise<void>;
}

declare module "next-auth/jwt" {
  export interface JWT {
    email?: string | null;
  }
}

declare module "next-auth/providers/credentials" {
  export interface CredentialsConfig {
    name?: string;
    credentials?: Record<string, unknown>;
    authorize?: (credentials: Record<string, unknown> | undefined) => Promise<unknown> | unknown;
  }
  export default function CredentialsProvider(config: CredentialsConfig): unknown;
}

export {};
