# Next.js App Router Reference

> Freshness: targets Next.js 16+. Verify against https://nextjs.org/docs before relying on specific APIs.

## Routing

### File-based conventions
```
app/
  layout.tsx          # Root layout (required)
  page.tsx            # Home (/)
  loading.tsx         # Route-level Suspense fallback
  error.tsx           # Route-level error boundary
  not-found.tsx       # Custom 404
  (marketing)/        # Route group (no URL segment)
    about/page.tsx    # /about
  (dashboard)/
    layout.tsx        # Dashboard layout
    @sidebar/page.tsx # Parallel route (named slot)
    @main/page.tsx
  products/
    [id]/page.tsx     # /products/123 (dynamic)
    [...slug]/page.tsx # Catch-all
  api/items/route.ts  # Route handler
```

- **Route groups** `(name)`: separate layouts without URL impact.
- **Parallel routes** `@slot`: render multiple pages in one layout.
- **Intercepting routes** `(.)`, `(..)`, `(...)`: show content in different context (e.g., modal).

## Rendering Strategies

These two caching models are mutually exclusive per project, set once in `next.config` by whether `cacheComponents` is on. Do not mix examples across them.

### Legacy model (`cacheComponents` off -- the Next.js 15 default, still the default on 16)

```tsx
export default function About() { return <h1>About</h1>; }

export async function generateStaticParams() {
  return (await getProducts()).map(p => ({ id: p.id }));
}
```

Dynamic SSR opts in via `cookies()`, `headers()`, `searchParams`, or `export const dynamic = 'force-dynamic'`. ISR uses `export const revalidate = 3600` (seconds). These three route segment configs (`dynamic`, `revalidate`, `fetchCache`) are only valid in this model.

### Cache Components model (`cacheComponents: true`, Next.js 16+)

```ts
// next.config.ts
import type { NextConfig } from 'next';

export default { cacheComponents: true } satisfies NextConfig;
```

Static shell + dynamic holes, replacing the removed `experimental.ppr` / `experimental.dynamicIO` flags. Once this flag is on, `dynamic`, `revalidate`, and `fetchCache` **error at build** instead of doing anything -- see `frontend-react-nextjs/SKILL.md` Step 4 for the `use cache`/`cacheLife` mapping. Read runtime data (`cookies()`, `headers()`, `searchParams`) inside a `<Suspense>`-wrapped component instead of at the top of the page.

### Streaming SSR (either model)
```tsx
export default function Page() {
  return (
    <main>
      <h1>Dashboard</h1>
      <Suspense fallback={<ChartSkeleton />}>
        <SlowChart />
      </Suspense>
    </main>
  );
}
```

## Caching (Four Layers)

| Layer | Scope | Invalidation |
|-------|-------|-------------|
| Request memoization | Single request (deduped fetch) | Automatic |
| Data cache | Persistent fetch results | `revalidatePath()`, `revalidateTag()`, time-based |
| Full route cache | Pre-rendered HTML + RSC payload | Redeployment, revalidation |
| Router cache | Client session (30s dynamic, 5min static) | `router.refresh()` |

Legacy model:
```tsx
fetch(url, { next: { revalidate: 3600 } });           // Time-based
fetch(url, { next: { tags: ['products'] } });          // Tag-based
revalidateTag('products', 'max');                       // Invalidate by tag -- 2nd arg is a required cache profile
fetch(url, { cache: 'no-store' });                     // No cache
```

Cache Components model: move the `fetch` options into a `'use cache'` function and call `cacheLife()`/`cacheTag()` instead (see `frontend-react-nextjs/SKILL.md` Step 3-4). `updateTag('products')` (Server Actions only) expires a tag immediately, for read-your-own-writes, instead of `revalidateTag`'s stale-while-revalidate.

## Server Actions

```tsx
'use server';
export async function createItem(formData: FormData) {
  const title = formData.get('title') as string;
  await db.items.create({ title });
  revalidatePath('/items');
  redirect('/items');
}
```

```tsx
// In a form
<form action={createItem}>
  <input name="title" required />
  <SubmitButton />
</form>
```

## Proxy (Next.js 16)

Single `proxy.ts` at project root, runs before every matched request. Next.js 16 deprecates the `middleware` filename and named export; Proxy uses the Node.js runtime.
```tsx
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function proxy(request: NextRequest) {
  if (!request.cookies.get('session') && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  return NextResponse.next();
}
export const config = { matcher: ['/dashboard/:path*'] };
```

## Metadata API
```tsx
export const metadata = { title: 'My App', description: '...', openGraph: { title: 'My App', images: ['/og.jpg'] } };

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props) {
  const { id } = await params;
  const product = await getProduct(id);
  return { title: product.name, description: product.summary };
}
```

## Official Documentation
- App Router: https://nextjs.org/docs/app
- Caching: https://nextjs.org/docs/app/building-your-application/caching
- Server Actions: https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations
- Rendering: https://nextjs.org/docs/app/building-your-application/rendering
- Proxy: https://nextjs.org/docs/app/getting-started/proxy
- Metadata: https://nextjs.org/docs/app/api-reference/functions/generate-metadata
