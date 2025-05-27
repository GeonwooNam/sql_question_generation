style2desc = {
    "Formal": '''**Formal Style**
- Uses standard grammar and vocabulary.
- Example: Find all students older than 18 years and return their home addresses.''',

    "Colloquial": '''**Colloquial Style**
- Employs informal vocabulary and expressions.
- Example: Hey! Could you help me find all the students who are over 18? I'd love to know their names and where they live.''',

    "Imperative": '''**Imperative Style**
- Uses command or directive sentences.
- Example: Could you please gather all the students who are older than 18? I really need to know their names and where they live!''',

    "Interrogative": '''**Interrogative Style**
- Uses question forms.
- Example: Could you tell me which students are older than 18 and what their home addresses are?''',

    "Descriptive": '''**Descriptive Style**
- Uses detailed descriptions with contextual information.
- Example: I want to know the names and home addresses of all students older than 18.''',

    "Concise": '''**Concise Style**
- Use short sentences.
- Example: Students older than 18, return their names and addresses.''',

    "Vague": '''**Vague Style**
- Includes ambiguous vocabulary requiring inference.
- Example: What are the names and addresses of those older students? (External Knowledge: 'older students' refers to age >= 18.)''',

    "Metaphorical": '''**Metaphorical Style**
- Uses metaphors or metaphorical expressions.
- Example: Find the names and addresses of those who have reached adulthood. (External Knowledge: 'reached adulthood' refers to age >= 18.)''',

    "Multi-turn Dialogue": '''**Multi-turn Dialogue Style**
- This involves a dialogue to clarify the user's query needs.
- Example: [{"User": "I want to query some student information."}, {"Assistant": "Which students' information would you like to query?"}, {"User": "Students older than 18."}, {"Assistant": "What other information would you like to know about them?"}, {"User": "Names and addresses."}, {"Assistant": "Is there anything else you need?"}, {"User": "No."}, {"Assistant": "OK, I will help you translate your request into an SQL query."}]'''
}

step_map = {
    "wo_ek": '''
    1. **Explain the SQL Query:** Provide a detailed explanation of what the query does.
    2. **Generate a Question:** Formulate a natural language question based on the SQL query and explanation.
''',
    "w_ek":  '''
    1. **Explain the SQL Query:** Provide a detailed explanation of what the query does.
    2. **Generate a Question:** Formulate a natural language question based on the SQL query and explanation.
    3. **External Knowledge:** For Vague or Metaphorical styles, include external knowledge to enhance clarity.
''',
    "multi_round": '''
    1. **Explain the SQL Query:** Provide a detailed explanation of what the query does.
    2. **Generate a Dialogue:** Create a conversation between the User and the Assistant based on the SQL query and its explanation.
'''
}

guideline_map = {
    "wo_ek": '''1. Clearly describe the columns being selected by the SQL query. For example:
   - "SELECT * ... FROM ..." means "Find all ...";
   - "SELECT f.check_date, f.status, f.remarks, c.year, c.year_min, c.year_max, c.year_average, c.data_quality_score FROM ..." means "Return the check dates, statuses, remarks, years, minimum years, maximum years, average years, and quality scores for ...".
2. Ensure the natural language question accurately captures the semantics of the SQL query, including conditions such as predicates, `ORDER BY`, and `LIMIT` clauses.''',

    "w_ek": '''1. Clearly describe the columns being selected by the SQL query. For example:
   - "SELECT * ... FROM ..." means "Find all ...";
   - "SELECT f.check_date, f.status, f.remarks, c.year, c.year_min, c.year_max, c.year_average, c.data_quality_score FROM ..." means "Return the check dates, statuses, remarks, years, minimum years, maximum years, average years, and quality scores for ...".
2. Ensure the natural language question accurately captures the semantics of the SQL query, including conditions such as predicates, `ORDER BY`, and `LIMIT` clauses.
3. If necessary, incorporate external knowledge using multiple entries separated by semicolons (";"). These can include formulas, common sense, domain-specific knowledge, or extended context, such as information from long documents. Each entry should be concise.''',

    "multi_round": '''1. Clearly describe the columns being selected by the SQL query. For example:
   - "SELECT * ... FROM ..." means "Find all ...";
   - "SELECT f.check_date, f.status, f.remarks, c.year, c.year_min, c.year_max, c.year_average, c.data_quality_score FROM ..." means "Return the check dates, statuses, remarks, years, minimum years, maximum years, average years, and quality scores for ...".
2. Ensure the conversation accurately captures the semantics of the SQL query, including conditions such as predicates, `ORDER BY`, and `LIMIT` clauses.''',
}

output_format_map = {
    "wo_ek": '''Please structure your response as follows:

[EXPLANATION-START]
(SQL Explanation)
[EXPLANATION-END]

[QUESTION-START]
(Natural Language Question)
[QUESTION-END]

- **SQL Explanation**: Provide a clear and detailed explanation of the SQL query, enclosed within [EXPLANATION-START] and [EXPLANATION-END].
- **Natural Language Question**: Translate the SQL query into a natural language question, enclosed within [QUESTION-START] and [QUESTION-END].''',

    "w_ek": '''Please structure your response as follows:

[EXPLANATION-START]
(SQL Explanation)
[EXPLANATION-END]

[QUESTION-START]
(Natural Language Question)
[QUESTION-END]

[EXTERNAL-KNOWLEDGE-START]
(External Knowledge)
[EXTERNAL-KNOWLEDGE-END]

- **SQL Explanation**: Provide a clear and detailed explanation of the SQL query, enclosed within [EXPLANATION-START] and [EXPLANATION-END].
- **Natural Language Question**: Translate the SQL query into a natural language question, enclosed within [QUESTION-START] and [QUESTION-END].
- **External Knowledge**: Include any relevant external knowledge if applicable, enclosed within [EXTERNAL-KNOWLEDGE-START] and [EXTERNAL-KNOWLEDGE-END]. Leave this section blank if not needed.''',

    "multi_round": '''Please structure your response as follows:

[EXPLANATION-START]
(SQL Explanation)
[EXPLANATION-END]

[QUESTION-START]
(Natural Language Question, in the format of [{"User": ...}, {"Assistant": ...}, {"User": ...}, ....])
[QUESTION-END]

- **SQL Explanation**: Provide a clear and detailed explanation of the SQL query, enclosed within [EXPLANATION-START] and [EXPLANATION-END].
- **Natural Language Question**: Convert the SQL query into a multi-round dialogue, enclosed within [QUESTION-START] and [QUESTION-END]. Represent this as a list that captures multiple rounds of conversation between the User and the Assistant.''',
}

instruction_map = {
    "wo_ek": "Based on the above information, follow the reasoning steps to generate the explanation and the question corresponding to the SQL query.",
    "w_ek": "Based on the above information, follow the reasoning steps to generate the explanation, the question, and the external knowledge corresponding to the SQL query.",
    "multi_round": "Based on the above information, follow the reasoning steps to generate the explanation and the dialogue corresponding to the SQL query.",
}
