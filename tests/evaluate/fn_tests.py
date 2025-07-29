

###### has function for testing with real answer sheets

import os
import pdfplumber
import pytesseract
from dotenv import load_dotenv
load_dotenv()
import re
import json
import openai
from openai import OpenAI
import math

USE_OCR_IF_TEXT_EMPTY = True

### Extract and prepare qa_list, mark scheme

def extract_text_from_pdf(file_path):
    full_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
            elif USE_OCR_IF_TEXT_EMPTY:
                # OCR fallback
                image = page.to_image(resolution=300)
                pil_img = image.original
                ocr_text = pytesseract.image_to_string(pil_img)
                full_text += ocr_text + "\n"
    return full_text.strip()


def parse_questions_answers(text):
    """
    Parse a blob of Q&A text into structured list of (question, answer) pairs.
    Expects format: **Question N:** <question>\n**Student Answer:** <answer>
    """
    # 1) Remove all '**' so our markers line up
    clean = re.sub(r"\*+", "", text)

    # 2) Now match plain 'Question N:' and 'Answer:' or 'Student Answer:'
    pattern = re.compile(
        r"Question\s*(\d+):\s*"              # Question number
        r"(.*?)\s*"                          # Question text (lazy)
        r"(?:Student Answer|Answer):\s*"     # Either label
        r"(.*?)(?=\nQuestion\s*\d+:|\Z)",    # Answer up to next Question or end
        flags=re.DOTALL
    )

    qa_list = []
    for num, q, a in pattern.findall(clean):
        qa_list.append({
            "question_number": int(num),
            "question": q.strip(),
            "answer":   a.strip()
        })
    return qa_list


def get_max_marks(num_questions):
    """
    Prompt once for either:
      • A single integer to apply to all questions, or
      • Per-question marks in sequence from 1 to num_questions.
    Returns a dict: { question_index: max_marks }
    """
    # 1) Ask how many questions
    while True:
        n = input(f"How many questions are there? ").strip()
        if n.isdigit() and int(n) > 0:
            num = int(n)
            break
        print("  ↳ Please enter a positive integer.")

    # 2) Try uniform mark
    single = input(
        "All questions have the same max mark? "
        "Enter that mark (or press Enter to specify per question): "
    ).strip()
    if single.isdigit():
        uni = int(single)
        return {i: uni for i in range(1, num + 1)}

    # 3) Otherwise prompt one by one
    print("Enter max marks for each question (Enter to reuse previous):")
    marks = {}
    last = None
    for q in range(1, num + 1):
        prompt = f"  Q{q} max marks [{last if last is not None else ''}]: "
        val = input(prompt).strip()
        if val == "" and last is not None:
            marks[q] = last
        elif val.isdigit():
            marks[q] = int(val)
            last = marks[q]
        else:
            print("   ↳ Invalid input; defaulting to 0")
            marks[q] = 0
            last = 0
    return marks


def extract_qa(file_path, max_marks_dict):
    """
    1) Extract text & parse out qa_list (with question_number fields required)
    2) Annotate each qa_list entry with max_marks based on its question_number
    """
    answer_text = extract_text_from_pdf(file_path)
    qa_list     = parse_questions_answers(answer_text)

    # assign max_marks by question_number key
    for qa in qa_list:
        qnum = qa.get("question_number")
        qa["max_marks"] = max_marks_dict.get(qnum, 0)

    return qa_list, max_marks_dict


def extract_qa_main(pdf_folder, pdf_names):
    """
    Given a list of PDF filenames, runs extract_qa on each and returns
    two separate outputs:
      1) qa_dict: maps the base filename (no “.pdf”) to its qa_list
      2) max_marks_dict: the dict of max marks used for all PDFs
    """
    # Prompt once for max marks (shared across all PDFs)
    max_marks_dict = get_max_marks(None)

    qa_dict = {}
    for pdf_name in pdf_names:
        file_path = os.path.join(pdf_folder, pdf_name)
        qa_list, _ = extract_qa(file_path, max_marks_dict)
        key = os.path.splitext(pdf_name)[0]
        qa_dict[key] = qa_list

    return qa_dict, max_marks_dict



def create_mark_scheme(qa_dict, api_key, ms_prompt, model="gpt-4"):
    """
    Generate mark schemes for every distinct question number found across multiple QA lists,
    preserving each question's original number.

    """
    client = OpenAI(api_key=api_key)

    # 1) Build a map from question_number -> QA (first occurrence wins)
    qmap = {}
    for qa_list in qa_dict.values():
        for qa in qa_list:
            qn = qa["question_number"]
            if qn not in qmap:
                qmap[qn] = qa

    # 2) Create payload items sorted by question_number
    questions_payload = []
    for qn in sorted(qmap):
        qa = qmap[qn]
        item = {
            "question_number": qn,
            "question": qa["question"].strip()
        }
        if "max_marks" in qa:
            item["max_marks"] = qa["max_marks"]
        questions_payload.append(item)

    # 3) Serialize to JSON
    questions_json = json.dumps(questions_payload, indent=2)

    # 4) Inject into the MS prompt
    prompt = ms_prompt.replace("{questions_json}", questions_json)

    # 5) Single API call
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"user","content":prompt}],
        temperature=0.3
    )
    text = resp.choices[0].message.content

    # 6) Parse the JSON response
    try:
        ms_list = json.loads(text)
    except json.JSONDecodeError:
        arr_match = re.search(r"\[.*\]", text, flags=re.DOTALL)
        if not arr_match:
            raise ValueError(f"No JSON array found in response:\n{text}")
        ms_list = json.loads(arr_match.group(0))

    return ms_list


### Input manual scores

def input_manual_scores(qa_list):
    """
    Prompt the user to enter the true score for each question in qa_list.
    Returns a list of numeric values (int or float) in the same order as qa_list.
    """
    scores = []
    for qa in qa_list:
        qnum = qa["question_number"]
        while True:
            val = input(f"Enter manual score for question {qnum}: ").strip()
            try:
                # Try to parse as float (will accept integers too)
                score = float(val)
                scores.append(score)
                break
            except ValueError:
                print("  ↳ Invalid input; please enter a number (e.g., 3 or 3.5).")
    return scores


    ### Evaluate


def evaluate_answers(qa_list, ms_list, api_key, eval_prompt, model):
    """
    Batch‐evaluate student answers against their mark schemes using eval_prompt.
    """
    client = OpenAI(api_key=api_key)

    # Build payload: include both question data and scheme from ms_list
    eval_payload = []
    for qa, ms in zip(qa_list, ms_list):
        eval_payload.append({
            "question_number": qa["question_number"],
            "marks": qa.get("max_marks"),
            "question_text": qa["question"],
            "student_text": qa["answer"],
            "answer_template": ms["answer_template"],
            "marking_scheme": ms["marking_scheme"],
            "deductions": ms.get("deductions", []),
            "notes": ms.get("notes", "")
        })
    payload_json = json.dumps(eval_payload, indent=2)

    # Inject the payload into the eval prompt
    prompt = eval_prompt.format(payload_json=payload_json)

    # Single API call for batch evaluation
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    text = resp.choices[0].message.content

    # Parse the JSON array from the model's response
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        arr_match = re.search(r"\[.*\]", text, flags=re.DOTALL)
        if not arr_match:
            raise ValueError(f"No JSON array found in evaluation response:\n{text}")
        return json.loads(arr_match.group(0))


def extract_scores(eval_report):
    """
    Given the evaluation report (a list of dicts),
    return a list of the score values for each question.
    """
    return [item.get('score') for item in eval_report]


def calculate_smape(true_scores, pred_scores):
    """
    Compute the Symmetric Mean Absolute Percentage Error between two lists of scores.
    SMAPE handles zero values by using the sum of absolute values in the denominator.
    """
    if len(true_scores) != len(pred_scores):
        raise ValueError("Length mismatch between true and predicted score lists.")

    errors = []
    for t, p in zip(true_scores, pred_scores):
        denom = (abs(t) + abs(p))
        if denom == 0:
            # both true and pred are zero, define error as zero
            errors.append(0)
        else:
            errors.append(abs(p - t) / denom)

    # Multiply by 2 to match standard SMAPE definition, then average and percentage
    return (sum(errors) * 100) / len(errors) * 2


def calculate_nrmse(true_scores, pred_scores, qa_list, max_marks_dict):
    """
    Compute the normalized Root Mean Squared Error (nRMSE) as a percentage.

    nRMSE = 100 * sqrt( (1/N) * sum( ((t_i - p_i) / M_i)**2 ) )
    """
    max_marks = [max_marks_dict[qa["question_number"]] for qa in qa_list]
    if not (len(true_scores) == len(pred_scores) == len(max_marks)):
        raise ValueError("All three lists must have the same length.")

    n = len(true_scores)
    if n == 0:
        raise ValueError("Input lists must not be empty.")

    # sum of squared normalized errors
    sse_norm = 0.0
    for t, p, M in zip(true_scores, pred_scores, max_marks):
        if M == 0:
            raise ValueError("Maximum mark for a question cannot be zero.")
        err_norm = (t - p) / M
        sse_norm += err_norm * err_norm

    mse_norm = sse_norm / n
    nrmse_pct = math.sqrt(mse_norm) * 100
    return nrmse_pct


def calculate_nmae(true_scores, pred_scores, qa_list, max_marks_dict):
    max_marks = [max_marks_dict[qa["question_number"]] for qa in qa_list]

    if not (len(true_scores) == len(pred_scores) == len(max_marks)):
      raise ValueError("All three lists must have the same length.")

    n = len(true_scores)
    if n == 0:
        raise ValueError("Input lists must not be empty.")

    N = len(true_scores)
    errors = [abs(t - p)/M for t, p, M in zip(true_scores, pred_scores, max_marks)]
    return 100 * sum(errors) / N


def evaluate_main(file_path, model, qa_list, max_marks_dict, ms_list, scores_manual=None,
         scores_auto=None):

    metric_autoic_manual = None
    metric_auto = None

    # Evaluate
    eval_report = evaluate_answers(qa_list, ms_list, OPENAI_API_KEY, eval_prompt, model)
    scores = extract_scores(eval_report)
    max_marks = [max_marks_dict[qa["question_number"]] for qa in qa_list]

    if scores_manual is not None:
      # Compare with manual and get metrics
      metric_manual = calculate_nmae(scores_manual, scores, qa_list, max_marks_dict)
      print("metric_manual", metric_manual)
    if scores_auto is not None:
      # Compare with auto and get metrics
      metric_auto = calculate_nmae(scores_auto, scores, qa_list, max_marks_dict)
      print("metric_auto", metric_auto)

    return eval_report, scores, metric_manual, metric_auto


def save_augmented_report(qa_list, scores_manual, eval_report, filename,
                          folder_path=OUTPUT_FOLDER):
    """
    Merge qa_list, scores_manual, and eval_report into one JSON file.

    Each entry will contain, in order:
      1) all fields from the qa_list dict
      2) 'score_manual' from scores_manual
      3) all fields from the corresponding eval_report dict

    The result is saved to folder_path/answer_name(.json).
    """
    # ensure output folder exists
    os.makedirs(folder_path, exist_ok=True)

    # ensure .json extension
    base = filename if filename.lower().endswith(".json") else filename + ".json"
    out_path = os.path.join(folder_path, base)

    combined = []
    for qa, manual_score, eval_item in zip(qa_list, scores_manual, eval_report):
        entry = {}
        # 1) qa_list fields
        for k, v in qa.items():
            entry[k] = v
        # 2) manual score
        entry['score_manual'] = manual_score
        # 3) eval_report fields
        for k, v in eval_item.items():
            entry[k] = v
        combined.append(entry)

    # write to disk
    with open(out_path, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"Saved augmented report to {out_path}")


 ### Save results into csv

 def append_results(log_path, file_id, metric_manual, metric_auto, scores,
                         fresh=False):
    """
    Append a row of SMAPE results to a CSV log, with separate manual and auto columns.

        smape_manual:  Sequence of SMAPE values for manual comparisons.
        smape_auto:    Sequence of SMAPE values for automatic comparisons.
    """
    if fresh and os.path.isfile(log_path):
        os.remove(log_path)

    # Ensure parent directory exists
    directory = os.path.dirname(log_path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)

    file_exists = os.path.isfile(log_path)

    with open(log_path, mode='a', newline='') as f:
        writer = csv.writer(f)

        # Write header only on first run
        if not file_exists:
            header = ['file_id']
            header += [f'manual_{i+1}' for i in range(len(metric_manual))]
            header += [f'auto_{j+1}'   for j in range(len(metric_auto))]
            # one column per score‐list
            header += [f'score_{k+1}'       for k in range(len(scores))]
            # one column per score‐list total
            header += [f'score_total_{k+1}' for k in range(len(scores))]
            writer.writerow(header)

        # 4) Build the row: flatten manual/auto, JSON‐dump each scores list, then totals
        row = [file_id, *metric_manual, *metric_auto]
        row += [json.dumps(score_list) for score_list in scores]
        row += [sum(score_list) for score_list in scores]
        writer.writerow(row)



def read_smape_log(log_path):
    """
    Read the SMAPE log CSV into a pandas DataFrame.
    """
    return pd.read_csv(log_path)

