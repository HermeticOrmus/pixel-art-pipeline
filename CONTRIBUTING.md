# Contributing to pixel-art-pipeline

Thank you for your interest in contributing. This project follows the **Gold Hat Philosophy**: every contribution should empower users, never extract from them.

## Before You Contribute

Ask yourself:
- Does this change **empower** the user?
- Does it operate **transparently**?
- Does it respect **user autonomy**?

If yes to all three, we'd love your contribution.

## How to Contribute

### Reporting Issues

- Use GitHub Issues
- Include your OS, shell, and relevant version info
- Provide steps to reproduce
- Include actual vs expected behavior

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly (especially `--dry-run` mode)
5. Commit with conventional format: `type(scope): description`
6. Push and open a Pull Request

### Commit Format

```
type(scope): description

Types: feat, fix, docs, refactor, test, chore
```

Examples:
- `feat(generator): add parallel batch processing`
- `fix(assembler): handle missing frames gracefully`
- `docs(readme): add config examples`

## Code Standards

- **Clarity > Cleverness** -- write code others can understand
- **Safety first** -- always default to dry-run/preview mode
- **Test destructive operations** -- never delete without confirmation
- **Cross-platform** -- consider Windows, macOS, and Linux

## Gold Hat Guidelines

We reject contributions that:
- Add telemetry or tracking without explicit user consent
- Implement dark patterns or manipulative UX
- Compromise user privacy or security
- Add unnecessary complexity

We welcome contributions that:
- Fix bugs or improve reliability
- Add useful features with clear documentation
- Improve cross-platform compatibility
- Make the tool more accessible

---

> *"Build what elevates. Reject what degrades."*
