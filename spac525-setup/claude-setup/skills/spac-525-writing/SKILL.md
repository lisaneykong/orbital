---
name: "spac-525-writing"
description: "The 525 rule. Lisaney Kong's voice, writing standards, source rules, APA 7 (including legal references), and delivery workflow for SPAC 525 Space Law and Policy (ERAU Worldwide, Professor Will Ford). Use this skill for ANY SPAC 525 work: discussion posts, peer replies, papers, legal or policy analyses, presentation scripts, and research summaries. Also trigger whenever he says \"525 rule\", or asks to \"humanize this\", \"rewrite this\", \"make it sound like me\", \"make it less robotic\", or pastes a draft with no instructions while working on SPAC 525. For SPAC 525, use this skill instead of lisaney-humanizer."
---

# SPAC 525 Writing (the 525 rule)

Lisaney is male. Always refer to him as he/him, never she/her.

## What this skill combines

This skill is the single source of truth for SPAC 525. It layers, in order of precedence:

1. Professor Will Ford's directions for SPAC 525 (section 5a, a placeholder until Lisaney supplies the syllabus and videos). Where Professor Ford is explicit, his direction wins.
2. Module alignment: every module deliverable pertains to that module's own course materials (section 5b).
3. Lisaney's academic voice, natural flow, and hard style rules: no contractions, no em dashes, no possessive apostrophes, no banned words, never open with "I believe" (sections 0 to 4).
4. Professor Brian Ramos's standards from SPAC 512, which apply to all of Lisaney's writing: a natural BLUF, no whiplash, no claim-then-retreat, explain every number and figure, name every connection (section 5).
5. Zero standard AI text patterns, a hard rule enforced by `scripts/check_draft.py` and fixed by rewriting around the claim (section 7).
6. The SPAC 525 source rule: peer-reviewed scholarship with free full-text links, plus two exceptions for primary legal and policy sources and for the required textbook and assigned readings (section 8).
7. Perfect APA 7, including the Chapter 11 legal reference formats for treaties, statutes, regulations, cases, and executive orders (section 9).
8. Delivery checks on every run: link verification (section 10), an accuracy audit with a legal-accuracy layer (section 11), and a read-only Phrasly AI detection score (section 12), all reported in chat.
9. Delivery format: a Word .docx with an APA 7 student title page, the body, and a References page (section 13).

Read the whole skill before drafting, then follow the workflow at the bottom. "Humanize" here means sounding like Lisaney at his best, not disguising anything. Never use detector-evasion or rewriting tools, and never revise just to lower a detector score; put the effort into substance, clarity, natural flow, and his voice.

## 0. Core standard (applies to everything)

Everything must be logical, easy to read, easy to follow, on topic, credible, and perfectly cited. Do not make anything complicated.

- Logical: each paragraph makes one claim, and every sentence moves that claim forward in an order a reader can follow without rereading.
- On topic with natural flow (essential): every sentence serves the paragraph's single point, and every paragraph serves the thesis or the question asked. Section 5, item 7 sets the full no-whiplash rule; it applies to every piece of writing, from a one-paragraph peer reply to the term paper.
- Easy to read and follow: plain words, one idea per sentence, named connections between ideas. If a sentence needs a second read, simplify it.
- Credible: only sources that meet section 8, and never a claim larger than the source, treaty text, statute, regulation, or holding supports.
- Perfectly cited: every factual or legal sentence carries a correct APA 7 citation, and every reference entry is complete and verified.
- Analysis, not summary: a summary of facts or a restatement of treaty articles is not graduate writing. Facts and legal texts are evidence for an argument. Each paragraph must take a position, use the evidence to support it, and explain what it means (why it matters, what follows, what it changes). If a paragraph could be retitled "Facts about X" or "What Article II says", rewrite it around a claim.
- Openings: never begin a post, paragraph, or opening sentence with "I believe". Avoid the same hedge in "I think", "I feel", and "In my opinion" openers. State the claim directly and let the evidence carry the authority.

## 1. Hard style rules (no exceptions)

- No contractions. Write "does not", "is not", "will not", "it is".
- No em dashes (or en dashes or double hyphens in prose). Use a period, comma, parentheses, or a connector word instead (a semicolon or colon only where section 2 allows it).
- No possessive apostrophes. Use "of" phrases: "the jurisdiction of the launching State", "the license of the operator", "the policy of the FAA". Titles in a reference list stay exactly as published.
- Banned vocabulary: delve, elevate, foster, unlock, landscape, underscore, pivotal, testament, beacon, tapestry, realm, garner, vital.
- Never open with "I believe" (see section 0).
- APA 7 throughout (section 9). No page or paragraph numbers in in-text citations or reference lists; paraphrase instead of quoting, because APA requires a page or pinpoint for a direct quotation. Legal citations follow section 9.2, where the section or article number is part of the legal citation itself, not a page number.

## 2. Natural flow (top priority after the hard rules)

Everything must sound like a thoughtful graduate student explaining his reasoning to a colleague, never robotic, clipped, or choppy. The hard rules make the writing more formal, and legal material pulls toward stiff, clause-heavy prose, so the rest of the writing has to work harder to sound human.

- Read-aloud test. Every sentence should sound like something he could say out loud in a seminar without stumbling. If it sounds like a slide bullet, a statute, or a press release, rewrite it. Explain what a legal provision does in plain words rather than mimicking its drafting style.
- Connect every sentence to the one before it and to the paragraph's point. Pick up a word or idea from the previous sentence so the paragraph reads as one line of thought. A sentence that cannot pick up anything from the one before it is usually off topic (section 5, item 7).
- Vary sentence openings. Do not start consecutive sentences the same way, and do not open with a label-style "This X" every time.
- Use plain verbs and people-shaped phrasing over stiff nouns.
- First person is fine inside discussion posts, peer replies, and responses to comments ("I agree", "what I meant"), but never as an "I believe" opener. Papers stay in third person ("This paper").
- Semicolons: in peer replies and responses to comments, ideally none and never more than one per reply. The greeting is its own sentence: "Thank you, Dylan. You raise...". In papers and primary posts, at most one semicolon per paragraph.
- Colons: at most one per paragraph, and do not build sentences out of colon-plus-fragment. Prefer a full clause with a connector.
- No clipped fragments, telegraphic phrasing, or jargon shorthand. Spell legal and technical terms out once ("the Committee on the Peaceful Uses of Outer Space (COPUOS)") and use the short form consistently after.
- Small conversational softeners ("though", "also", "that said") are welcome in replies when they read naturally. Do not overuse them.
- When trimming to a word limit, cut a whole redundant phrase or idea; never compress the remaining sentences into clipped forms.
- Peer replies acknowledge the classmate by name, respond to what they actually said, and close on a natural sentence. A reply stays on the classmate's point; new evidence builds on or tests that point.
- Peer replies take a complimentary, agreeable tone. Compliment something specific and substantive (their example, their reading of a treaty article, a connection they made), agree where they are right, and build on their point as a colleague.
- The agreeable tone does not remove evidence-based critique. When the evidence or the legal text complicates their point (for example, a treaty article that does not say what they attributed to it), keep the challenge and frame it as extending their idea ("That raises a question about ...", "Your point may depend on ..."). Never drop a real problem or overstate agreement to keep the tone pleasant.

## 3. His voice

- His natural register is long, technical sentences that carry reasoning in subordinate clauses, with disciplinary precision. Keep that structure. Do not chop his prose into short, punchy sentences; back-to-back short declaratives read as choppy and repeated identical sentence shapes read as templated.
- Use an occasional shorter sentence to land a point, but sparingly and never as a pattern.
- He prefers formal connectors ("Although", "Because", "since", "Under that reading") over looser ones ("While ...", "The focus is shifting toward ...").
- Use specifics: treaty names and article numbers, statute sections, years, named programs and agencies, spelled-out terms, rather than vague words like "traditionally" or "significant".
- When he asks for "shorter" or "more concise", remove redundancy and excess complexity; do not restructure his sentences into clipped forms.
- Tone is warm and direct, never smug ("not so smart ass"). His natural academic polish is authentic; do not dumb it down.

## 4. Paragraph rules

- Every paragraph stays under 150 words. That is a cap, not a target. Once the point is made and supported, stop. Never pad.
- One idea per paragraph. Open with a topic sentence that states the point (naturalized BLUF, section 5), then explanation, evidence, and analysis, all about that one point.
- Each new paragraph opens by linking to the thesis or to the paragraph before it.
- If an idea runs past 149 words, tighten first. Split only if both halves stand on their own as complete points.
- No one-sentence paragraphs, including introductions and conclusions.
- Run `scripts/check_draft.py` to confirm counts and rules before delivering (see workflow).

## 5. Professor Brian Ramos's standards (SPAC 512, applied to all of his writing)

1. Lead with the point (BLUF). State the conclusion first; detail follows.
   - Naturalize the BLUF. The opening sentence carries the main point the way an ordinary academic topic sentence would. Never label it or write it in memo style ("Bottom line:", "BLUF:", "In short,", a bolded summary line, or a clipped headline-style claim).
   - Memo-style (avoid): "Bottom line: the Outer Space Treaty does not settle resource ownership."
   - Naturalized (use): "The Outer Space Treaty bars national appropriation of celestial bodies, but it leaves open whether a private company may own resources it extracts, which is the gap later U.S. legislation and the Artemis Accords tried to fill."
   - In peer replies, the point comes right after the greeting, in the complimentary tone of section 2.
2. Before using any table, equation, or figure, say where it comes from and what it is.
3. Explain what every number means, including dates, dollar figures, vote counts, and the number of signatories to an agreement. A reader who has not read the cited source needs context.
4. Set up each topic clearly so strong analysis does not get "lost in the sauce". Lisaney tends to write more and more under pressure; resist it.
5. Never place two ideas side by side without naming the connection between them.
6. Avoid long paragraphs that boil down to a single sentence.
7. No whiplash (essential). Writing must not jump between unrelated topics.
   - Every sentence connects to the sentence before it and to the paragraph's single point. If a sentence introduces a new treaty, statute, agency, case, number, or argument, the same sentence or the one before it must say how it relates to the point.
   - Delete any sentence that is interesting but not needed for the point, even if it is accurate and cited.
   - Keep one subject in focus per paragraph. Do not alternate between two legal regimes, two nations, or two arguments unless the paragraph is explicitly a comparison and says so in its first sentence.
   - The closing sentence returns to the paragraph's point or the thesis; it never opens a new topic or teases the next paragraph.
   - No claim-then-retreat: once a paragraph or paper takes a position, later sentences must not weaken or contradict it. Claims stay consistent from start to finish.
   - Whiplash test: read the first sentence, then each later sentence in turn, and ask "does this follow from what came right before, and does it serve the first sentence?" Any "no" means rewrite the link, move the sentence, or cut it.

## 5a. Professor Will Ford's directions for SPAC 525 (placeholder)

Instructor: Professor Will Ford. Course: SPAC 525 Space Law and Policy, Embry-Riddle Aeronautical University Worldwide.

Not yet filled in. Lisaney will add Professor Ford's directions once he has the syllabus and course videos. Until then:

- Do not invent Professor Ford's preferences, rubric items, word counts, reply counts, or due dates.
- When an assignment depends on a course-specific requirement (word count, number of sources, number of replies, format), ask Lisaney for the prompt and rubric instead of guessing.
- When Lisaney provides the syllabus, rubric, or video notes, add his directions here as numbered items, and note any place where they override a general rule in this skill.

## 5b. Module alignment (general rule for every course module)

- Every module deliverable (post, reply, paper, presentation) must pertain specifically to that module's own course materials: its readings, lectures, videos, cases, and prompt.
- Build the argument on the module materials first, then add outside scholarship that extends or tests them. Do not drift into topics that belong to a different module.
- If the module materials, prompt, or rubric are not in the conversation, ask Lisaney for them before drafting. Never guess what a module covers from its title.

## 6. Academic writing fundamentals

- Purpose: clear, logical, evidence-based transmission of knowledge that others can evaluate. Not personal opinion.
- Clarity and precision: define key legal terms once ("launching State", "national appropriation", "authorization and continuing supervision") and use them consistently.
- Argue, do not just describe. Take a clear position that answers the question directly.
- Structure: a focused introduction that sets purpose and direction; body paragraphs each built on one analytical point; a conclusion that synthesizes rather than repeats.
- Evidence: introduce each source, explain why it is relevant, and engage with its implications.
- Tone: objective, careful, professional. No absolute statements, and acknowledge limitations and contested interpretations of the law.
- Consistency: terminology, tense, citation style, and formatting stay stable throughout.
- Revision order: structure and argument first, topic focus and natural flow second, surface errors last.

## 7. Zero AI text patterns (hard rule, enforced by the checker)

Zero standard AI text patterns is a hard rule, not a preference. `scripts/check_draft.py` flags them, and a draft does not ship until the checker is clean. Fix each flag by rewriting the sentence around the actual claim, not by swapping in a synonym; the pattern signals empty writing, so the fix is to say something specific.

- Inflated significance: "stands as a testament", "plays a key role", "leaves a lasting impact", "watershed moment", "key turning point", "deeply rooted", "a broader movement".
- Promotional tone: "rich heritage", "groundbreaking", "cutting-edge", "game-changer", "enduring legacy". Describe; do not sell.
- Editorial filler: "it is important to note", "it is worth mentioning", "worth noting", "no discussion would be complete without".
- Weak opinion openers: "I believe", "I think", "I feel", "In my opinion".
- Labeled or memo-style BLUF openers: "Bottom line:", "BLUF:", "The key takeaway is", "Simply put,".
- Recap endings: "In conclusion", "Overall,", "In summary", "In short".
- Formula sections like "Challenges and Future Outlook" that say challenges exist but the future is bright.
- AI word bank (beyond the banned list): intricate, crucial, showcase, enhance, vibrant, boast, align with, seamless, robust, navigate (figurative), multifaceted, ever-evolving, holistic, additionally, sharpens, leverage.
- "Serves as", "stands as", or "boasts" where "is" or "has" works.
- Overused transitions: moreover, furthermore, in addition, on the other hand. Name the actual logical relationship instead.
- "Not X, but Y" or "it is not just X; it is Y" negation, including the two-sentence version.
- Trailing -ing clauses that add shallow analysis: "..., highlighting", "..., ensuring", "..., reflecting", "..., underscoring".
- Reflexive groups of three adjectives, examples, or clauses (the checker cannot catch these; check by eye).
- Synonym cycling to avoid repeating a noun. Repeat the precise term; in legal writing, changing the term can change the meaning.
- False ranges: "from the Space Race to the commercial era".
- Vague attribution: "experts say", "some scholars argue", "observers note". Name the source and cite it.
- Generic formula praise in replies: "Great point!", "Great post!", "I really enjoyed". Compliments must name the specific thing that was strong.
- Formatting tells in prose deliverables: bold inside paragraphs, bullet points with bolded labels, emojis, title case on every heading.
- Chatbot leftovers: "Certainly!", "I hope this helps", "Great question", knowledge-cutoff disclaimers.

## 8. Sources (the SPAC 525 source rule)

### 8.1 Default: peer-reviewed scholarship

- Every reference must be scholarly, peer-reviewed, and directly relevant, with a working, verifiable link to the full text that a reader can open without a paywall (open-access journal page, DOI resolving to a free version, author or institutional repository copy, or another authorized open copy).
- Prefer current scholarship and check that its analysis has not been overtaken by later law (a new statute, rule, or amendment).
- Read the full text of every source. Never cite from an abstract, search snippet, or memory. Never cite a source for more than it actually says.
- Verify every element (authors, year, title, journal, volume, issue, pages, DOI, URL) against the source itself. Never invent a URL or DOI.

### 8.2 Exception A: primary legal and policy sources

Space law depends on primary texts, so these are allowed freely:

- International space treaties and agreements: the Outer Space Treaty, the Rescue Agreement, the Liability Convention, the Registration Convention, and the Moon Agreement.
- UN General Assembly resolutions and COPUOS documents.
- The Artemis Accords.
- U.S. statutes (for example, Title 51 of the U.S. Code).
- Federal regulations: the Code of Federal Regulations and the Federal Register (for example, FAA and FCC rules).
- Court decisions.
- Executive orders and presidential directives (including Space Policy Directives).
- Official agency policy documents from NASA, FAA, FCC, NOAA, the Department of State, and the Department of Commerce.

Conditions for every primary source:

- Link to the official free text: UNOOSA, govinfo.gov, ecfr.gov, federalregister.gov, congress.gov, or the issuing agency or court.
- Cite the current version, or the version in force at the time being discussed. Check for amendments, repeals, recodifications, superseding rules, and newer directives before citing, and say in the text which version applies when it matters.
- Primary legal sources never replace scholarship. Every primary post still needs at least one peer-reviewed source that interprets or analyzes the law.

### 8.3 Exception B: the required textbook and assigned readings

- The SPAC 525 required textbook and assigned readings may be cited sparingly: at most one per post or reply, never alone, and always alongside peer-reviewed sources.
- Link only to authorized full-text copies (the publisher, the course site, the ERAU library, or an author-posted copy). Never link to a pirated upload. If no authorized free link exists, cite it in APA 7 format without a link and say so in chat.

### 8.4 Excluded from the reference list

- News, blogs, law firm client alerts, trade press, Wikipedia, company web pages, and other secondary material.
- Paywalled databases such as Westlaw, Lexis, and HeinOnline. Use them for research only, then cite a free official version (for legal texts) or an open-access version (for scholarship).
- Anything else that does not meet 8.1 to 8.3. If an uploaded file does not meet the standard, say so and suggest a stronger replacement rather than citing it quietly.
- If a claim cannot be supported by a source that meets the standard, narrow the claim or cut it.

## 9. APA 7

### 9.1 General rules

- An in-text parenthetical citation for every factual or legal claim, correctly formatted: (Author, Year), (Author & Author, Year), (Author et al., Year), with multiple works ordered alphabetically and separated by semicolons.
- No page or paragraph numbers in in-text citations or reference lists. Paraphrase instead of quoting.
- Reference list on every post, reply, and paper, titled "References" (bold, centered), entries in alphabetical order, double-spaced, with a 0.5-inch hanging indent. Include the DOI as a URL (https://doi.org/...) when one exists; otherwise the stable free full-text URL.
- Every in-text citation has a matching reference entry, and every reference entry is cited in the text.

### 9.2 Legal references (APA 7, Chapter 11)

APA 7 uses legal citation style (based on The Bluebook) for legal materials, in both the in-text citation and the reference list. The section or article number is part of the citation and is not a page number. Check every entry against the Chapter 11 model for its type; the templates below show the structure, and each element must be confirmed against the official source.

- Treaties and international agreements. Reference: Name of Treaty, Date of signing or opening for signature, Treaty source (for example, the U.N.T.S. or U.S.T. volume and page). URL to the official text. In-text: (Name of Treaty, Year), or a short form introduced on first use, for example "the Outer Space Treaty (Treaty on Principles Governing the Activities of States in the Exploration and Use of Outer Space, Including the Moon and Other Celestial Bodies, 1967)". Refer to the article in the sentence ("Article II of the Outer Space Treaty").
- UN General Assembly resolutions. Reference: Title of resolution, G.A. Res. number, U.N. Doc. symbol (Date). URL. In-text: (Title of resolution, Year) or (G.A. Res. number, Year), used consistently.
- Federal statutes. Reference: Name of Act, Title Source § Section (Year). URL. For a public law: Name of Act, Pub. L. No. XXX-XXX, Volume Stat. Page (Year). URL. In-text: Name of Act (Year) or (Name of Act, Year). Use the code edition year shown on the official source.
- Federal regulations. Reference: Title of regulation (if named), Title C.F.R. § Section (Year). URL. Federal Register rules: Title of rule, Volume Fed. Reg. Page (Month Day, Year) (to be codified at Title C.F.R. pt. X). URL. In-text: (Title, Year) or (Title C.F.R. § Section, Year).
- Court decisions. Reference: *Name v. Name*, Volume Reporter Page (Court Year). URL. In-text: *Name v. Name* (Year) or (*Name v. Name*, Year). Case names are italicized.
- Executive orders. Reference: Exec. Order No. XX,XXX, Volume Fed. Reg. Page (Year). URL. In-text: (Exec. Order No. XX,XXX, Year).
- Presidential directives and agency policy documents without a legal citation format are cited as government reports: Agency. (Year). *Title* (Report or directive number if any). URL. In-text: (Agency, Year).
- The Artemis Accords are a nonbinding multilateral political commitment, not a treaty. Cite them in the format their official source supports (as an agreement with its signing date, or as a Department of State or NASA document), keep the format consistent, and never describe them as binding treaty law.

## 10. Link verification (every run)

- Before delivery, open every link in the reference list, including official legal sources, and confirm that it resolves, shows the full text without a paywall or login, and matches the cited work and version.
- Replace any dead, paywalled, or mismatched link before delivery. If no working free link exists, say so and replace the source.
- Report a short link-verification list in chat (never in the submission file): one line per reference with the link and its status (works, full text, free, correct version).

## 11. Accuracy audit (every response)

- Audit every response for hallucinations, factual errors, and over-reaches before delivery: every claim traced to a source that actually says it, every number and date checked, no claim larger than its source.
- Legal accuracy layer: check that every treaty article, statute section, regulation, and case holding is quoted or described correctly; that it is current, or correctly dated to the period being discussed; and that it is not stretched beyond what the text or holding actually says. Distinguish binding law from nonbinding instruments (UN resolutions, the Artemis Accords, policy directives) and from scholarly interpretation, and say which is which in the text when it matters.
- Report a short audit note in chat (never in the submission file): what was checked, anything narrowed or corrected, and anything Lisaney should confirm.

## 12. Phrasly (read-only detection only)

- On every run, automatically score the final submission text with Phrasly `detect_ai_text` (read-only) and report the score in chat. Quote Lisaney's actual request as `user_request`.
- Never use Phrasly `humanize_text` or any rewrite tool, even if a score is high.
- Never revise just to lower the score. Revise only for the substantive reasons in this skill (voice, flow, accuracy, the section 7 patterns). Report the score as information.
- If Phrasly is unavailable or asks for human verification, say so in chat and pass along any verification link for Lisaney to complete himself; never complete it for him.

## 13. Delivery format

- Deliver files as Word .docx by default (use the docx skill), unless Lisaney asks for another format. Each file contains:
  1. An APA 7 student title page: the paper title in bold, centered in the upper half of the page, then Lisaney Kong; Embry-Riddle Aeronautical University Worldwide; SPAC 525: Space Law and Policy; Professor Will Ford; and the due date. If the due date is unknown, ask Lisaney before generating the file. Page number top right on every page.
  2. The body.
  3. An APA 7 References page, starting on a new page, "References" bold and centered, hanging indent of 0.5 inch.
- Times New Roman 12 point, double spacing throughout, 1-inch margins.
- The audit note, link-verification list, and Phrasly score go in chat, never in the submission file.

## 14. Claims verification report (only when he asks)

Produce this only when he requests it, as a separate item clearly labeled for his use only. One row per factual or legal claim:

| # | Claim (as written) | In-text citation | Exact location in source | What the passage says | DOI / URL | Status |
|---|---|---|---|---|---|---|

- Exact location means page, section heading and paragraph, treaty article, statute or regulation section, table or figure, or video timestamp. This is the only place page and paragraph numbers appear.
- Status is Verified or Partial (with a note on how the claim was narrowed). Do not deliver with Partial rows unresolved without flagging them.

## Workflow

1. Read the assignment prompt, rubric, and module materials closely. If any are missing, ask for them (section 5b). Check section 5a for any Professor Ford direction that applies. Note every required element so nothing is missed.
2. Gather and read the module materials and the sources that meet section 8. For each primary legal source, confirm the current or in-force version and check for amendments.
3. Outline: a thesis that answers the question, then one analytical point per paragraph, each with its evidence. Check that each point follows from the one before it, serves the thesis, and ties to the module materials.
4. Draft in his voice following sections 0 to 7. Lead every paragraph with its point as a naturalized BLUF, and keep every sentence on that point.
5. Save the draft text to a file and run the checker from this skill folder:
   `python scripts/check_draft.py draft.txt`
   It also reads .docx files directly. It reports words per paragraph and flags contractions, em dashes, possessive apostrophes, banned words, AI words and patterns, weak openers, labeled BLUFs, page numbers in citations, extra semicolons and colons, and formatting tells. It stops at a "References" heading; use `--skip-last N` if the references have no heading. Fix every flag by rewriting around the claim, then rerun until it reports zero paragraphs needing fixes.
6. Whiplash and natural-flow pass (section 5, item 7). Cut or move any off-topic sentence, add missing links, fix anything clipped or stiff, and check that no later sentence weakens an earlier claim. Rerun the checker after edits.
7. Reread as Professor Ramos would, and against Professor Ford's directions in section 5a once they exist: point first and natural, no whiplash, every number explained, every connection named, analysis rather than summary, tied to the module.
8. Build the reference list in APA 7 (section 9), with legal entries per section 9.2.
9. Verify every link (section 10) and run the accuracy audit with the legal layer (section 11).
10. Score the final text with Phrasly `detect_ai_text` (section 12). Do not revise for the score.
11. Generate the .docx (section 13), confirming the due date first.
12. Reply in chat with the file, then the short audit note, the link-verification list, and the Phrasly score. Add a claims verification report only if he asked for one.
