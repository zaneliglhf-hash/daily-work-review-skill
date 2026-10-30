![Daily work review](assets/cover.svg)

[简体中文](README.md) · [English](README.en.md)

# Daily Work Review Skill

Reusable instructions for checking submissions, reading original works, filling existing ✅/❌ table options, and producing a Chinese review report. **The review date is the target work date; never subtract a day.** The skill and report template are in Chinese.

**Write limits in 0.1.1: a skill provides instructions, not permissions.** Automatic writeback requires verified table permissions or a constrained write tool that prevents the executor from modifying anything outside the permitted cells for this run. Without that boundary, the executor reads, reviews, produces the report and a proposed per-person write list, and leaves the source table unchanged. Screenshot coordinates alone must not be used to type text or range addresses into a Canvas table. [Write boundary rules](skills/daily-work-review/references/write-safety.md), in Chinese.

## 1. Copy this installation request to your executor

```text
Install the Daily Work Review skill from
https://github.com/zaneliglhf-hash/daily-work-review-skill

Read INSTALL.md first. Download skills/daily-work-review with all its
referenced files and install it using this executor's supported method.
Check file integrity and whether the host recognizes the skill.
Check access to authenticated websites, original content, and constrained writeback.
Report missing capabilities honestly. Show the three-field daily form.
Do not start a real review during installation.
```

**Installation and recognition were verified for 0.1.0 in WorkBuddy 5.9.3. On 2026-10-30, a user reported unintended edits during a real-table trial; the complete writeback workflow failed. Live retesting of 0.1.1 is pending.** Installation does not establish safe writeback. [Verification scope](docs/verification.md).

An executor needs network access and file/skill installation capabilities. Otherwise download the [Skill ZIP](dist/daily-work-review.zip) and import it through the host's skill manager. The ZIP does not include a model or browser.

If an older version is installed, copy this into a new task:

```text
Update the Daily Work Review skill following INSTALL.md at
https://github.com/zaneliglhf-hash/daily-work-review-skill
Download the complete package, verify its manifest and file hashes, and preserve personal configuration.
Confirm that the write boundary rules from 0.1.1 or later are loaded; refresh skills and start a new conversation if needed.
Only update and check the skill. Do not open, repair or fill any review table, or resume an interrupted task.
```

## 2. Use it daily

```text
使用「每日作品审核」Skill。

审核链接：
审核日期：2026-10-28
本次审核人：

请核对提交情况、填写审核表，并生成完整审核汇报。
```

Provide the submission and audit table links in **审核链接** on first use. If only one is given, the agent looks for the other table's explicit link, then asks if it is missing. Group configuration may be saved in your own workspace for reuse. **审核日期** is the target date and report title date. **本次审核人** is the reviewer, not the author being reviewed. Tomorrow's reviewer is the next person in the source rotation; tomorrow's calendar date comes from the actual execution date.

All members are checked. By default, five distinct authors are reviewed in source order. Add `本次点评：@同学甲 @同学乙` to choose authors without narrowing attendance checks. Handle sign-in yourself when prompted, and copy the finished report to your group manually.

## Expected report

```text
10月28日审核同步

未完成人员名单；@姓名

作品1 @作者
这篇帖子的优点是……；缺点是……。

明日审核人：@姓名
审核情况：原审核表链接
```

This is a format illustration, not a real review. Execution status is reported separately. Missing content must not become invented feedback; incomplete submission evidence must not become ❌.

## Executed exercise

![Synthetic table after native-option writeback and refresh](assets/demo-table.png)

For 0.1.0, an independent executor checked eight synthetic members, read five full texts, and filled the existing options. Refresh preserved six ✅ and two ❌, with the previous day unchanged. [Report generated during that test](examples/sample-report.txt), in Chinese. This earlier simulated-table test does not establish compatibility with WeCom Docs or verify the write boundary introduced in 0.1.1.

## Compatibility and limits

A standard skill does not make every chat app capable of installing skills or controlling a browser. Browser access alone is insufficient for safe writeback: permissions must actually constrain the executing account, or a tool that cannot be bypassed must check the document, sheet, cells and allowed values. Without this boundary, the workflow stays read-only and supplies a proposed write list. Material-only tools require the full roster, submissions and original text/images, and must state that online access and writeback were not performed.

[Installation](INSTALL.md) · [Compatibility](docs/compatibility.md) · [Verification](docs/verification.md) · [Synthetic exercise](examples/README.md) — these detailed documents are in Chinese.

Start with a test table. Quotas come from the host; this project has no built-in API and promises no unlimited free usage. Never commit private table links, credentials or real review records, including in public issues.
