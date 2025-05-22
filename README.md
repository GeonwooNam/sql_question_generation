# Data Generation Framework

This repository contains the source code and prompts for our data synthesis framework.  
Based on OmniSQL's data synthesis framework, with custom modifications and enhancements.  
For more details for OmniSQL, please refer to https://github.com/RUCKBReasoning/OmniSQL/tree/main


- **Step 1:** Complexity-Aware SQL Query Generation (see `sql_generation`)
- **Step 2:** Stylized Natural Language Question Synthesis (see `question_generation`)
- **Step 3:** Score the evaluation score by comparing our model's sql query output to the answer query(Step 1) for a given question(Step 2) (see `evaluation`)

These steps are designed to be sequential, but you may begin from any intermediate step depending on your data.

To set up the Anaconda environment for data generation:

```bash
conda create -n data_generation python=3.9.5
conda activate data_generation

pip install -U sentence-transformers
pip install json-repair ijson matplotlib func_timeout
```

Once again, special thanks to RUCKBReasoning for making excellent framework OmniSQL. (Unauthorized redistribution is strictly prohibited)