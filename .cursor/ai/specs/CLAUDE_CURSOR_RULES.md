# AI Assistant Rules for Cursor IDE

## CRITICAL: Minimal Change Protocol
1. **IDENTIFY**: Exact 2-5 lines causing the issue - change NOTHING else
2. **JUSTIFY**: Why does working code need modification? If you can't justify, don't change it
3. **SCOPE**: Fix only the broken part - never "improve while we're at it"
4. **FORBIDDEN**: Touching working systems while fixing unrelated problems

## File Operations
- **Paths**: Use `./path/to/file.py` format for repository files (following AI_CURSOR_INTEGRATION.md)
- **Changes**: One file per response maximum
- **Validation**: Ask user before modifying any file they've said "works" or "is proven"

## Code Blocks
```language:./exact/file/path
// ... existing code ...
{{ minimal change description }}
// ... existing code ...
```

## Commands
```bash
cd /absolute/path/to/directory
command_here
```
- Always use absolute paths for `cd`
- Never open new terminals unless requested

## Pre-Change Checklist (MANDATORY)
- [ ] Is this the minimal change needed?
- [ ] Am I touching working functionality?
- [ ] Can I fix this with <5 line changes?
- [ ] Did user say this part works?

## RED FLAGS - STOP IMMEDIATELY
- Rewriting working scripts
- "Comprehensive" solutions  
- Multiple system changes for one problem
- User said "this works" but I want to change it

## Apply Button Protocol
- Verify target file before user clicks Apply
- If wrong file targeted, user should change active file in editor