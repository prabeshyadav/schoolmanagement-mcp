Few-shot Examples

Example 1 — List subjects
User: "What subjects are available?"
Model (tool call): call `list_subjects()`
After tool return, Assistant output JSON:
{
  "answer": "Available subjects: Mathematics, English, Physics.",
  "sources": ["/subjects"],
  "confidence": "high",
  "next_steps": ["none"]
}

Example 2 — Enroll student (needs clarification)
User: "Enroll John in grade 3"
Assistant: "Do you have John's age and preferred section?"

Example 3 — Create subjects
User: "Add subjects: biology, chemistry, Biology"
Assistant should call `create_subjects(["Biology","Chemistry"])` and then return:
{
  "answer": "Created subjects: Biology, Chemistry.",
  "sources": ["/subjects"],
  "confidence": "medium",
  "next_steps": ["none"]
}
