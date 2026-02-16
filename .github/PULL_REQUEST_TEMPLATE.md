## Description

Brief description of the changes and their motivation.

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Accessibility improvement
- [ ] Performance improvement
- [ ] Refactoring (no functional changes)

## Accessibility Impact

- [ ] No accessibility impact
- [ ] Improves accessibility (describe how)
- [ ] New UI elements have proper ARIA labels and keyboard navigation
- [ ] Tested with screen reader
- [ ] WCAG AAA contrast ratios verified

## Testing

- [ ] Backend tests pass (`uv run pytest`)
- [ ] Agent tests pass (`cd agents && uv run pytest`)
- [ ] Frontend tests pass (`pnpm test`)
- [ ] New tests added for this change

## Quality Gates

- [ ] `uv run ruff check .` — clean
- [ ] `uv run mypy .` — clean
- [ ] `pnpm lint` — clean
- [ ] `pnpm typecheck` — clean
- [ ] Docker Compose builds and runs (`docker compose up -d --build`)

## Screenshots

If UI changes, include before/after screenshots.

## Related Issues

Closes #(issue number)
