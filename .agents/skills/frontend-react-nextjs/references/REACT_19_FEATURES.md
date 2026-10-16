# React 19 Features Reference

> Freshness: targets React 19 (stable Dec 2024). Verify against https://react.dev/blog and https://react.dev/reference before relying on specific APIs.

## New Hooks

### use()
Unwrap promises and context values during render. Replaces useEffect-based data fetching patterns for client components.
```tsx
// Unwrap a promise passed from a server component
function Comments({ commentsPromise }: { commentsPromise: Promise<Comment[]> }) {
  const comments = use(commentsPromise); // suspends until resolved
  return <ul>{comments.map(c => <li key={c.id}>{c.text}</li>)}</ul>;
}

// Read context without useContext
function Theme() {
  const theme = use(ThemeContext);
  return <div style={{ color: theme.fg }}>...</div>;
}
```
Key: `use()` can be called conditionally (inside if/loops), unlike other hooks.

### useActionState (replaces useFormState)
Manage form state from server action results. Returns [state, formAction, isPending].
```tsx
async function updateProfile(prevState: State, formData: FormData) {
  'use server';
  const name = formData.get('name');
  if (!name) return { error: 'Name is required' };
  await db.update({ name });
  return { success: true };
}

function ProfileForm() {
  const [state, action, isPending] = useActionState(updateProfile, {});
  return (
    <form action={action}>
      <input name="name" />
      {state.error && <p>{state.error}</p>}
      <button disabled={isPending}>Save</button>
    </form>
  );
}
```

### useFormStatus
Access pending state of the parent form. Must be used inside a component rendered within a `<form>`.
```tsx
function SubmitButton() {
  const { pending } = useFormStatus();
  return <button disabled={pending}>{pending ? 'Saving...' : 'Save'}</button>;
}
```

### useOptimistic
Show optimistic UI while a server action is in flight. Reverts automatically on error.
```tsx
function TodoList({ todos }: { todos: Todo[] }) {
  const [optimisticTodos, addOptimistic] = useOptimistic(
    todos,
    (state, newTodo: Todo) => [...state, newTodo]
  );

  async function addTodo(formData: FormData) {
    const todo = { id: crypto.randomUUID(), text: formData.get('text') as string };
    addOptimistic(todo);
    await createTodo(todo); // server action
  }

  return (
    <form action={addTodo}>
      <input name="text" />
      <button>Add</button>
      <ul>{optimisticTodos.map(t => <li key={t.id}>{t.text}</li>)}</ul>
    </form>
  );
}
```

## Actions

Actions are functions that use async transitions to handle form submissions and mutations.

### Server Actions
Define with `'use server'` directive. Called from forms or programmatically.
```tsx
// In a separate file or inline
async function deleteItem(id: string) {
  'use server';
  await db.items.delete(id);
  revalidatePath('/items');
}

// In a form
<form action={deleteItem.bind(null, item.id)}>
  <button>Delete</button>
</form>

// Programmatically with useTransition
const [isPending, startTransition] = useTransition();
startTransition(() => deleteItem(id));
```

### Form actions
`<form action={fn}>` accepts async functions directly. Combined with useActionState for state management.

## Suspense Improvements

### Streaming with nested boundaries
```tsx
<Suspense fallback={<PageSkeleton />}>
  <Header />
  <Suspense fallback={<SidebarSkeleton />}>
    <Sidebar />
  </Suspense>
  <Suspense fallback={<ContentSkeleton />}>
    <MainContent />
  </Suspense>
</Suspense>
```
Each boundary streams independently. HTML arrives progressively as data resolves.

### Server Components + Suspense
Server components can be async. Wrap slow data fetches in Suspense for streaming:
```tsx
// This component is a server component (no 'use client')
async function ProductDetails({ id }: { id: string }) {
  const product = await getProduct(id); // slow fetch
  return <div>{product.name}</div>;
}

// Parent streams the shell while ProductDetails loads
<Suspense fallback={<Skeleton />}>
  <ProductDetails id={params.id} />
</Suspense>
```

## Other Changes

### ref as prop
No more `forwardRef`. Refs are regular props in React 19:
```tsx
function Input({ ref, ...props }: { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} {...props} />;
}
```

### Metadata in components
`<title>`, `<meta>`, `<link>` in any component are automatically hoisted to `<head>`:
```tsx
function BlogPost({ post }: { post: Post }) {
  return (
    <>
      <title>{post.title}</title>
      <meta name="description" content={post.summary} />
      <article>{post.content}</article>
    </>
  );
}
```

### Improved error reporting
React 19 deduplicates and improves error messages, including better hydration mismatch warnings.

## Official Documentation
- React 19 blog post: https://react.dev/blog/2024/12/05/react-19
- Hooks reference: https://react.dev/reference/react
- Server Components: https://react.dev/reference/rsc/server-components
- Server Actions: https://react.dev/reference/rsc/server-actions
