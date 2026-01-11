#!/usr/bin/env python3
"""
Populate the Learning Targets sheet with detailed FA25 information.

This script updates the existing Learning Targets sheet to add columns for:
- F_Description (Foundational description)
- F_Objectives (Foundational learning objectives, newline-separated)
- Adv_Description (Advanced description)
- Adv_Objectives (Advanced learning objectives, newline-separated)
- Notes (additional notes)

Usage:
    python populate_lt_details.py
"""

import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# FA25 Learning Target Details (from Google Doc 1hIQsMJ9pq7Ttuy-cSkC41BLM0kv9SIG5hYgks5fY44k)
LT_DETAILS = {
    "LT1": {
        "title": "Algebra Skills",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in essential algebra skills including solving equations, factoring, and simplifying algebraic expressions.",
        "f_objectives": [
            "Simplify expressions using distributive property and order of operations",
            "Add, subtract, and simplify rational expressions",
            "Solve linear equations",
            "Solve quadratic equations by factoring",
        ],
        "adv_description": "Demonstrate proficiency in using rules of exponents. Demonstrate proficiency in solving inequalities.",
        "adv_objectives": [
            "Simplify rational expressions using exponent rules",
            "Solve quadratic and polynomial inequalities",
            "Express inequality solutions using number lines, interval notation, and set builder notation",
        ],
    },
    "LT2": {
        "title": "Functions",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in using and understanding functions with emphasis on relationships given graphically.",
        "f_objectives": [
            "Identify variables and parameters in models",
            "Describe function behavior from graphs",
            "Use function notation for verbal descriptions",
            "Evaluate functions graphically",
            "Use graphs to solve equations and inequalities",
            "Sketch graphical models from verbal descriptions",
            "Identify relationships expressed as functions",
        ],
        "adv_description": "Demonstrate proficiency in using and understanding functions with emphasis on relationships given algebraically.",
        "adv_objectives": [
            "Identify variables and parameters in formula-based models",
            "Evaluate functions at numerical and algebraic inputs",
            "Evaluate piecewise-defined functions",
            "Understand function notation and units",
            "Find natural domain from formulas",
            "Evaluate and create composite functions",
        ],
    },
    "LT3": {
        "title": "Linear Functions",
        "type": "Two-Part",
        "f_description": "Create linear functions from given data and demonstrate proficiency in translating between different forms of a linear equation.",
        "f_objectives": [
            "Compute slope from linear data",
            "Find line equations from table or graph data",
            "Identify linear vs. non-linear relationships",
            "Translate between point-slope and point-intercept forms",
        ],
        "adv_description": "Build a linear model from a verbal description and reason about proportional change in an application.",
        "adv_objectives": [
            "Identify slope in verbal descriptions of proportional change",
            "Build linear models from verbal descriptions",
            "Determine slope units in applications",
            "Reason about proportional change using slope",
        ],
    },
    "LT4": {
        "title": "Discrete Time Dynamical Systems",
        "type": "Two-Part",
        "f_description": "Demonstrate an understanding of sequences and the terminology of discrete time models.",
        "f_objectives": [
            "Identify sequence terms using index notation",
            "Compute sequence terms from index functions",
            "Express patterns using sequence notation",
            "Understand discrete time dynamical systems terminology",
            "Use updating functions and initial states",
            "Understand connections between function composition and repeated application",
        ],
        "adv_description": "Modeling with Discrete Time Dynamical Systems.",
        "adv_objectives": [
            "Create updating functions from verbal descriptions",
            "Find equilibrium solutions",
            "Reason about equilibrium behavior",
            "Verify closed-form and equilibrium solutions",
        ],
    },
    "LT5": {
        "title": "Exponentials and Logarithms",
        "type": "Two-Part",
        "f_description": "Create discrete time models of exponential decay.",
        "f_objectives": [
            "Recognize discrete exponential growth and decay models",
            "Build updating rules from verbal descriptions",
            "Create closed-form solutions from updating rules",
            "Transform discrete to continuous exponential models",
        ],
        "adv_description": "Modeling with Discrete Time Dynamical Systems.",
        "adv_objectives": [
            "Evaluate logarithmic expressions",
            "Apply logarithm rules to expand or combine expressions",
            "Use logarithms to solve exponential equations",
            "Reason about exponential growth and decay",
        ],
    },
    "LT6": {
        "title": "Trigonometry and Periodic Functions",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in evaluating and understanding trigonometric ratios using right triangles and the unit circle.",
        "f_objectives": [
            "Use Pythagorean Theorem for right triangles",
            "Compute sine, cosine, and tangent for right triangles",
            "Identify coordinates on the unit circle with sine and cosine",
            "Use reference angles to find trigonometric values",
            "Recognize angles corresponding to unit circle positions",
        ],
        "adv_description": "Demonstrate proficiency in building and interpreting sine and cosine models of periodic behavior.",
        "adv_objectives": [
            "Construct sine/cosine models by identifying amplitude, vertical shift, and period",
            "Determine period, minimum, and maximum values",
            "Interpret periodic parameters in applied contexts with units",
        ],
    },
    "LT7": {
        "title": "Log Transformations",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in identifying exponential and power functions using log transformations and interpreting their linearized forms.",
        "f_objectives": [
            "Identify exponential and power relationships from log-linear and log-log axes",
            "Apply logarithmic transformation to express exponential functions as linear",
            "Apply logarithmic transformation to express power functions as linear",
        ],
        "adv_description": "Demonstrate proficiency in constructing exponential and power functions from linearized graphs using log transformations.",
        "adv_objectives": [
            "Construct exponential functions from linear log-linear plots",
            "Construct power functions from linear log-log plots",
            "Use exponentiation to express functions from linearized forms",
        ],
    },
    "LT8": {
        "title": "Limits",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in evaluating graphical limits and reasoning about end behavior of functions.",
        "f_objectives": [
            "Estimate one-sided and two-sided limits from graphs",
            "Use limits at infinity for rational function end behavior",
            "Analyze composite function behavior with exponential components",
            "Analyze long-term behavior of exponential functions",
        ],
        "adv_description": "Demonstrate proficiency in reasoning about continuity and evaluating limits using proper notation and algebraic techniques.",
        "adv_objectives": [
            "Determine parameter values ensuring continuity",
            "Use correct limit notation",
            "Identify and evaluate indeterminate forms",
            "Identify vertical asymptotes or holes",
            "Recognize and apply L'Hopital's Rule",
        ],
    },
    "LT9": {
        "title": "Rates of Change",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in computing and interpreting average and instantaneous rates of change from graphical and tabular data.",
        "f_objectives": [
            "Compute average rate of change from tables",
            "Estimate average rate of change from graphs",
            "Identify average rate of change as secant line slope",
            "Identify instantaneous rate of change as tangent line slope",
            "Compute instantaneous rate of change from graphs",
        ],
        "adv_description": "Demonstrate proficiency in interpreting instantaneous rate of change as a limit and estimating it using average rates of change.",
        "adv_objectives": [
            "Interpret instantaneous rate of change as limiting average rates",
            "Approximate instantaneous rates using average rates",
            "Use instantaneous rates to approximate nearby function values",
        ],
    },
    "LT10": {
        "title": "Definition of the Derivative",
        "type": "One-Time",
        "f_description": "Demonstrate proficiency in using and interpreting the limit definition of the derivative.",
        "f_objectives": [
            "State the limit definition of the derivative",
            "Use limit definition to compute derivatives of quadratic functions",
            "Compare derivative results with basic rules",
            "Interpret derivatives as limits of secant line slopes",
        ],
    },
    "LT11": {
        "title": "Basic Derivative Rules",
        "type": "One-Time",
        "f_description": "Demonstrate proficiency in computing derivatives using basic rules, including examples involving parameters.",
        "f_objectives": [
            "Apply power rule including fractional and negative exponents",
            "Apply power rule to parameterized functions",
            "Use exponential rule for exponential differentiation",
            "Apply derivative rules for sine and cosine",
            "Differentiate natural logarithm functions",
        ],
    },
    "LT12": {
        "title": "Graphical Differentiation",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in interpreting derivative information from the graph of a function.",
        "f_objectives": [
            "Match function graphs to derivative graphs",
            "Identify points where derivative equals zero",
            "Indicate derivative signs at given points",
            "Estimate derivative values",
        ],
        "adv_description": "Demonstrate proficiency in sketching the graph of the derivative from the graph of a function.",
        "adv_objectives": [
            "Sketch derivative graphs from function graphs",
        ],
    },
    "LT13": {
        "title": "The Chain Rule",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in applying the chain rule to compute derivatives of composite functions in different representations.",
        "f_objectives": [
            "Apply chain rule to formulas",
            "Compute composite function derivatives from tabular data",
            "Apply chain rule to graphical functions",
        ],
        "adv_description": "Demonstrate proficiency in interpreting and applying the chain rule using Leibniz notation in applications.",
        "adv_objectives": [
            "Use Leibniz notation for derivative representation and computation",
            "Apply units correctly in chain rule applications",
            "Interpret chain rule results in context",
        ],
    },
    "LT14": {
        "title": "Product and Quotient Rules",
        "type": "One-Time",
        "f_description": "Demonstrate proficiency in applying the product and quotient rules to compute derivatives of functions.",
        "f_objectives": [
            "Apply product rule to products",
            "Apply quotient rule to quotients",
            "Apply rules to graphical and tabular functions",
            "Apply rules to parameterized functions",
            "Compute derivatives at specific points from verbal descriptions",
        ],
    },
    "LT15": {
        "title": "Linear Approximation",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in creating and using linear approximations.",
        "f_objectives": [
            "Construct linear approximations from function and derivative data",
            "Create linear approximations using derivative rules",
            "Use approximations to estimate nearby function values",
        ],
        "adv_description": "Demonstrate proficiency in creating and using linear approximations for functions defined as solutions to differential equations.",
        "adv_objectives": [
            "Compute linear approximations for differential equation solutions",
            "Use approximations for estimation",
            "Understand linear approximation for numerical differential equation solutions",
        ],
    },
    "LT16": {
        "title": "Implicit Differentiation and Related Rates",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in using implicit differentiation and applying implicit differentiation.",
        "f_objectives": [
            "Use implicit differentiation for instantaneous rate of change expressions",
            "Evaluate rates of change at specific points",
            "Determine points where slope is undefined",
            "Create relationships between rates",
            "Reason about related rates in applications",
        ],
        "adv_description": "TBD",
        "adv_objectives": [],
    },
    "LT17": {
        "title": "Graphical Applications of the Derivative",
        "type": "Two-Part",
        "f_description": "Use the first and second derivatives to find intervals of monotonicity and concavity. Identify critical points, local extrema, and inflection points.",
        "f_objectives": [
            "Sketch graphs using first and second derivative signs",
            "Determine critical points",
            "Apply first derivative test for local extrema",
            "Identify derivative signs from graphs",
        ],
        "adv_description": "Demonstrate proficiency in computing and using the second derivative to determine concavity and identify inflection points.",
        "adv_objectives": [
            "Compute second derivatives of polynomials",
            "Determine concavity intervals from second derivatives",
            "Identify inflection point locations",
            "Use second derivative test for extrema locations",
        ],
    },
    "LT18": {
        "title": "Antiderivative Rules",
        "type": "One-Time",
        "f_description": "Demonstrate proficiency in computing antiderivatives using basic rules.",
        "f_objectives": [
            "Compute general antiderivatives using power rule",
            "Use exponential antiderivative rule",
            "Apply sine and cosine antiderivative rules",
            "Find antiderivative of reciprocal function",
            "Solve initial value problems",
        ],
    },
    "LT19": {
        "title": "Riemann Sums and Accumulated Change",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in using summation notation and in using Riemann sums to estimate definite integrals.",
        "f_objectives": [
            "Write finite series terms from summation notation",
            "Express Riemann sums using summation notation",
            "Use Riemann sums for integral estimation",
            "Describe improvement methods for estimates",
            "Write integrals as Riemann sum limits",
            "Understand definite integral limit notation",
        ],
        "adv_description": "Demonstrate an understanding of the connection between signed area and accumulated change in an application.",
        "adv_objectives": [
            "Compute net change from rate of change graphs",
            "Determine area and accumulated change units",
            "Locate local extrema from rate graphs",
            "Estimate function values from rate graphs and initial values",
        ],
    },
    "LT20": {
        "title": "The Definite Integral",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in computing definite integrals using antiderivatives, signed area, and properties of the definite integral.",
        "f_objectives": [
            "Use Evaluation Theorem for integral computation",
            "Use integral properties for linear combinations",
            "Compute integrals using signed area",
        ],
        "adv_description": "Demonstrate proficiency in conceptual understanding of the definite integral.",
        "adv_objectives": [
            "Distinguish definite integrals as numbers vs. indefinite as families",
            "Describe antiderivative use in Evaluation Theorem",
            "Construct definite integrals from verbal descriptions",
            "Determine integral units in applications",
            "Compute integrals using signed area and formulas",
            "Understand integral properties over intervals",
        ],
    },
    "LT21": {
        "title": "The Fundamental Theorem of Calculus",
        "type": "One-Time",
        "f_description": "Use the Fundamental Theorem of Calculus and demonstrate an understanding of a definite integral as net change.",
        "f_objectives": [
            "Use Fundamental Theorem to compute rates of change",
            "Create and interpret net change integral representations",
            "Estimate function values from rate graphs",
        ],
    },
    "LT22": {
        "title": "Integration by Substitution",
        "type": "One-Time",
        "f_description": "Demonstrate proficiency in performing integration by substitution.",
        "f_objectives": [
            "Understand substitution-chain rule relationship",
            "Use substitution for indefinite integrals",
            "Make variable changes in definite integrals",
            "Compute definite integrals via substitution",
        ],
    },
    "LT23": {
        "title": "Derivative and Antiderivative Techniques",
        "type": "One-Time",
        "f_description": "Review derivative and antiderivative rules.",
        "f_objectives": [
            "Compute derivatives using basic rules",
            "Combine product rule and chain rule",
            "Compute indefinite integrals using basic rules",
        ],
    },
    "LT24": {
        "title": "Local and Global Extrema",
        "type": "One-Time",
        "f_description": "Demonstrate proficiency in identifying local and global extrema.",
        "f_objectives": [
            "Use first or second derivative tests for local extrema",
            "Combine Fundamental Theorem with derivative tests",
            "Apply closed-interval method for global extrema",
        ],
    },
    "LT25": {
        "title": "Optimization",
        "type": "Group",
        "f_description": "Demonstrate proficiency in problem solving skills related to optimization.",
        "f_objectives": [
            "Create objective functions from verbal descriptions",
            "Identify objective functions and constraints",
            "Use constraints to develop single-variable functions",
            "Find and interpret global maxima",
        ],
        "notes": "This target involves collaborative learning during Week 15, combining classroom guidance with group-based problem-solving assessment.",
    },
}


def main():
    credentials_path = os.path.expanduser(os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", ""))
    sheet_id = os.environ.get("MATH140B_COURSE_CONFIG_ID", "")

    if not credentials_path or not sheet_id:
        print("Error: Set GOOGLE_SERVICE_ACCOUNT_FILE and MATH140B_COURSE_CONFIG_ID environment variables")
        return

    credentials = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet("Learning Targets")

    # Get current data
    all_values = worksheet.get_all_values()
    headers = all_values[0] if all_values else []

    print(f"Current columns: {headers}")

    # Determine which columns need to be added
    new_columns = ["F_Description", "F_Objectives", "Adv_Description", "Adv_Objectives", "Notes"]
    columns_to_add = [col for col in new_columns if col not in headers]

    if columns_to_add:
        print(f"Adding columns: {columns_to_add}")
        # Add new column headers
        start_col = len(headers) + 1
        for i, col_name in enumerate(columns_to_add):
            worksheet.update_cell(1, start_col + i, col_name)
            headers.append(col_name)
        print("Added new column headers")

    # Find column indices
    col_indices = {h: i + 1 for i, h in enumerate(headers)}
    lt_id_col = col_indices.get("LT_ID") or col_indices.get("LT ID")

    if not lt_id_col:
        print("Error: Could not find LT_ID or LT ID column")
        return

    # Get all LT IDs from sheet
    lt_ids = worksheet.col_values(lt_id_col)[1:]  # Skip header

    print(f"\nUpdating {len(lt_ids)} learning targets...")

    # Prepare batch update
    updates = []

    for row_idx, lt_id in enumerate(lt_ids, start=2):  # Row 2 is first data row
        if lt_id in LT_DETAILS:
            details = LT_DETAILS[lt_id]

            # Update each detail column
            if "F_Description" in col_indices and details.get("f_description"):
                updates.append({
                    "range": f"{gspread.utils.rowcol_to_a1(row_idx, col_indices['F_Description'])}",
                    "values": [[details["f_description"]]]
                })

            if "F_Objectives" in col_indices and details.get("f_objectives"):
                obj_text = "\n".join(details["f_objectives"])
                updates.append({
                    "range": f"{gspread.utils.rowcol_to_a1(row_idx, col_indices['F_Objectives'])}",
                    "values": [[obj_text]]
                })

            if "Adv_Description" in col_indices and details.get("adv_description"):
                updates.append({
                    "range": f"{gspread.utils.rowcol_to_a1(row_idx, col_indices['Adv_Description'])}",
                    "values": [[details["adv_description"]]]
                })

            if "Adv_Objectives" in col_indices and details.get("adv_objectives"):
                obj_text = "\n".join(details["adv_objectives"])
                updates.append({
                    "range": f"{gspread.utils.rowcol_to_a1(row_idx, col_indices['Adv_Objectives'])}",
                    "values": [[obj_text]]
                })

            if "Notes" in col_indices and details.get("notes"):
                updates.append({
                    "range": f"{gspread.utils.rowcol_to_a1(row_idx, col_indices['Notes'])}",
                    "values": [[details["notes"]]]
                })

            print(f"  Prepared update for {lt_id}: {details.get('title', 'Unknown')}")

    # Execute batch update
    if updates:
        print(f"\nExecuting {len(updates)} cell updates...")
        worksheet.batch_update(updates)
        print("Done!")
    else:
        print("No updates to make")


if __name__ == "__main__":
    main()
