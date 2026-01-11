#!/usr/bin/env python3
"""
Populate the Math 141B Learning Targets sheet with SP26 structure.

This incorporates changes from FA25:
- New LT5: Integration Techniques (review of LT1-4)
- Old LT5-9 shift to LT6-10
- Old LT10+LT11 combined into LT11: Phase Lines and Equilibrium Solutions
- LT12: Bifurcation Diagrams (now Group)
- New LT13: Integration Computation and Applications
- LT14-18: Vector Operations, Linear Transformations, Matrix Operations,
           Discrete Dynamical Systems, The Inverse Matrix
- LT19-25: Same as FA25

Usage:
    python populate_141b_lt_details.py
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

# SP26 Learning Target Details for Math 141B
LT_DETAILS = {
    "LT1": {
        "title": "Integration Review",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in computing definite integrals using antiderivatives, signed area, and properties of the definite integral.",
        "f_objectives": [
            "Use Evaluation Theorem for integral computation",
            "Apply antiderivative rules correctly",
            "Compute integrals using signed area",
            "Interpret net change in applications",
        ],
        "adv_description": "Demonstrate proficiency in conceptual understanding of the definite integral and its applications.",
        "adv_objectives": [
            "Distinguish definite integrals as numbers vs. indefinite as families",
            "Determine integral units in applications",
            "Construct definite integrals from verbal descriptions",
            "Understand integral properties over intervals",
        ],
    },
    "LT2": {
        "title": "Integration by Substitution",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in performing integration by substitution.",
        "f_objectives": [
            "Understand substitution-chain rule relationship",
            "Use substitution for indefinite integrals",
            "Identify appropriate substitutions",
        ],
        "adv_description": "Apply substitution method to definite integrals with proper change of variables.",
        "adv_objectives": [
            "Make variable changes in definite integrals",
            "Compute definite integrals via substitution",
            "Combine substitution with other techniques",
        ],
    },
    "LT3": {
        "title": "Integration by Parts",
        "type": "Two-Part",
        "f_description": "Use the integration by parts method to compute indefinite integrals.",
        "f_objectives": [
            "Apply integration by parts formula",
            "Choose appropriate u and dv",
            "Recognize when integration by parts is appropriate",
        ],
        "adv_description": "Use integration by parts to compute definite integrals and combine with other methods.",
        "adv_objectives": [
            "Compute definite integrals using integration by parts",
            "Apply tabular method for repeated integration by parts",
            "Combine integration by parts with other techniques",
        ],
    },
    "LT4": {
        "title": "Integration by Partial Fractions",
        "type": "Two-Part",
        "f_description": "Perform partial fraction decomposition for rational functions.",
        "f_objectives": [
            "Decompose rational functions into partial fractions",
            "Handle distinct linear factors",
            "Handle repeated linear factors",
        ],
        "adv_description": "Compute integrals using partial fraction decomposition.",
        "adv_objectives": [
            "Integrate rational functions using partial fractions",
            "Recognize when partial fractions is appropriate",
            "Combine with other integration techniques",
        ],
    },
    "LT5": {
        "title": "Integration Techniques",
        "type": "One-Time",
        "f_description": "Demonstrate proficiency in identifying and applying appropriate integration techniques from LT1-LT4.",
        "f_objectives": [
            "Identify which integration technique to apply",
            "Select between substitution, parts, and partial fractions",
            "Combine multiple techniques as needed",
            "Verify integration results by differentiation",
        ],
    },
    "LT6": {
        "title": "Modeling with Differential Equations",
        "type": "Two-Part",
        "f_description": "Create differential equation models from verbal descriptions.",
        "f_objectives": [
            "Create differential equation models from verbal descriptions",
            "Determine the order of a differential equation",
            "Distinguish autonomous from non-autonomous equations",
        ],
        "adv_description": "Verify solutions to differential equations.",
        "adv_objectives": [
            "Verify solutions for first-order differential equations",
            "Verify solutions for second-order differential equations",
            "Determine particular solutions from initial conditions",
        ],
    },
    "LT7": {
        "title": "Separation of Variables",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in identifying separable first-order differential equations.",
        "f_objectives": [
            "Identify separable vs. non-separable equations",
            "Separate variables algebraically",
            "Find general solutions in implicit form",
        ],
        "adv_description": "Solve separable differential equations and find particular solutions.",
        "adv_objectives": [
            "Find explicit solutions when possible",
            "Apply logarithm and exponentiation fluently",
            "Find particular solutions from initial conditions",
        ],
    },
    "LT8": {
        "title": "The Integrating Factor Method",
        "type": "Two-Part",
        "f_description": "Demonstrate understanding of the integrating factor method.",
        "f_objectives": [
            "Identify first-order linear differential equations",
            "Convert to standard form",
            "Compute the integrating factor",
        ],
        "adv_description": "Apply the integrating factor method to solve differential equations.",
        "adv_objectives": [
            "Understand connection to product rule derivative",
            "Find general solutions using integrating factors",
            "Find particular solutions from initial conditions",
        ],
    },
    "LT9": {
        "title": "Linear Models in Biology",
        "type": "One-Time",
        "f_description": "Construct differential equation models, find solutions, and interpret results in biological contexts.",
        "f_objectives": [
            "Construct differential equation models from biological scenarios",
            "Select appropriate solution technique",
            "Find general and particular solutions",
            "Interpret solutions in biological context",
        ],
        "notes": "Synthesis target combining modeling and solution techniques.",
    },
    "LT10": {
        "title": "Slope Fields",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in constructing slope fields for first-order differential equations.",
        "f_objectives": [
            "Sketch slope fields for differential equations",
            "Compute slopes at given points",
            "Identify nullclines",
        ],
        "adv_description": "Interpret slope fields and sketch solution curves.",
        "adv_objectives": [
            "Sketch solution curves on slope fields",
            "Recognize equilibrium solutions from slope fields",
            "Analyze long-term behavior from slope fields",
        ],
    },
    "LT11": {
        "title": "Phase Lines and Equilibrium Solutions",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in constructing phase lines and identifying equilibrium solutions.",
        "f_objectives": [
            "Construct phase lines for autonomous equations",
            "Determine equilibrium solutions",
            "Identify stable, unstable, and semi-stable equilibria",
        ],
        "adv_description": "Analyze equilibrium solutions and long-run behavior.",
        "adv_objectives": [
            "Classify stability of equilibrium solutions",
            "Verify equilibrium solutions algebraically",
            "Interpret equilibrium solutions in biological contexts",
            "Reason about long-run behavior across initial conditions",
        ],
    },
    "LT12": {
        "title": "Bifurcation Diagrams",
        "type": "Group",
        "f_description": "Demonstrate understanding of bifurcation diagrams and parameter effects on differential equation behavior.",
        "f_objectives": [
            "Sketch bifurcation diagrams",
            "Identify bifurcation values",
            "Describe qualitative behavior changes at bifurcations",
            "Analyze parameter effects on long-run behavior",
            "Understand tipping points and hysteresis",
        ],
        "notes": "Group assessment combining graphical analysis with parameter interpretation.",
    },
    "LT13": {
        "title": "Integration Computation and Applications",
        "type": "One-Time",
        "f_description": "Demonstrate proficiency in identifying and applying appropriate integration techniques in applied contexts.",
        "f_objectives": [
            "Select appropriate integration technique for a given problem",
            "Combine multiple integration techniques",
            "Apply integration to solve application problems",
            "Interpret integral results in context",
        ],
    },
    "LT14": {
        "title": "Vector Operations",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in fundamental vector operations.",
        "f_objectives": [
            "Compute linear combinations of vectors",
            "Calculate vector magnitudes",
            "Express vectors using standard basis vectors",
        ],
        "adv_description": "Apply vector operations in geometric and applied contexts.",
        "adv_objectives": [
            "Compute dot products",
            "Interpret vectors geometrically",
            "Plot vectors in the plane",
            "Apply scalar multiplication",
        ],
    },
    "LT15": {
        "title": "Linear Transformations",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency working with linear transformations.",
        "f_objectives": [
            "Verify linearity properties of transformations",
            "Apply linear transformations via basis vectors",
            "Identify domain and codomain dimensions",
        ],
        "adv_description": "Construct matrix representations of linear transformations.",
        "adv_objectives": [
            "Construct transformation matrices from descriptions",
            "Apply matrices to transform vectors",
            "Compose linear transformations using matrix multiplication",
        ],
    },
    "LT16": {
        "title": "Matrix Operations",
        "type": "Two-Part",
        "f_description": "Demonstrate proficiency in basic matrix operations.",
        "f_objectives": [
            "Perform matrix addition and subtraction",
            "Apply scalar multiplication",
            "Compute matrix-vector products",
        ],
        "adv_description": "Apply advanced matrix operations.",
        "adv_objectives": [
            "Compute matrix products",
            "Calculate matrix powers",
            "Apply distributive laws",
            "Recognize identity matrices",
        ],
    },
    "LT17": {
        "title": "Discrete Dynamical Systems",
        "type": "Two-Part",
        "f_description": "Create linear multivariable discrete time models from verbal descriptions.",
        "f_objectives": [
            "Create multivariable discrete time models",
            "Compute state vectors iteratively",
            "Plot sequences from discrete models",
        ],
        "adv_description": "Analyze and interpret discrete dynamical systems.",
        "adv_objectives": [
            "Interpret matrix coefficients in context",
            "Describe long-term behavior of discrete systems",
            "Connect to eigenvalue analysis",
        ],
    },
    "LT18": {
        "title": "The Inverse Matrix",
        "type": "Two-Part",
        "f_description": "Demonstrate understanding of inverse matrices.",
        "f_objectives": [
            "Verify if a matrix is invertible",
            "Compute inverses of 2x2 matrices",
            "Apply inverse matrices to solve systems",
        ],
        "adv_description": "Apply inverse matrices in modeling contexts.",
        "adv_objectives": [
            "Use inverse matrices in applications",
            "Understand relationship between inverse and determinant",
            "Apply inverse to matrix equations",
        ],
    },
    "LT19": {
        "title": "Gaussian Elimination",
        "type": "Two-Part",
        "f_description": "Represent systems using matrices and use row operations.",
        "f_objectives": [
            "Express systems as augmented matrices",
            "Identify row echelon form",
            "Apply elementary row operations",
        ],
        "adv_description": "Solve systems using Gaussian elimination.",
        "adv_objectives": [
            "Determine system consistency",
            "Apply back substitution",
            "Represent solution spaces",
            "Handle systems with free variables",
        ],
    },
    "LT20": {
        "title": "Eigenvalues and Eigenvectors",
        "type": "Two-Part",
        "f_description": "Compute eigenvalues and eigenvectors.",
        "f_objectives": [
            "Verify eigenvector-eigenvalue pairs",
            "Compute eigenvectors for given eigenvalues",
            "Find characteristic polynomials",
        ],
        "adv_description": "Apply eigenvalue analysis and understand geometric meaning.",
        "adv_objectives": [
            "Calculate determinants via cofactor expansion",
            "Explain geometric meaning of eigenvectors",
            "Recognize complex eigenvalues",
        ],
    },
    "LT21": {
        "title": "Solving Discrete Time Matrix Models",
        "type": "Two-Part",
        "f_description": "Find closed form solutions of iterated matrix models.",
        "f_objectives": [
            "Determine eigenvalues and eigenvectors of transition matrices",
            "Write general closed form solutions",
            "Decompose initial states into eigenvector components",
        ],
        "adv_description": "Analyze long-term behavior of discrete matrix models.",
        "adv_objectives": [
            "Determine stable distributions",
            "Interpret stable distributions in context",
            "Analyze convergence to equilibrium",
        ],
    },
    "LT22": {
        "title": "Markov Models",
        "type": "Two-Part",
        "f_description": "Create Markov models from verbal descriptions.",
        "f_objectives": [
            "Create transition diagrams",
            "Recognize stochastic matrices",
            "Identify regular stochastic matrices",
        ],
        "adv_description": "Analyze long-term behavior of Markov models.",
        "adv_objectives": [
            "Use dominant eigenvalue for long-run analysis",
            "Interpret stable distributions",
            "Analyze absorbing Markov models",
        ],
    },
    "LT23": {
        "title": "Interpreting Discrete Time Matrix Models",
        "type": "Two-Part",
        "f_description": "Use data from iterated matrix models to analyze behavior.",
        "f_objectives": [
            "Apply dominant eigenvalue to determine long-run behavior",
            "Interpret growth/decay rates",
            "Understand role of complex eigenvalues in oscillations",
        ],
        "adv_description": "Analyze parameter effects on model behavior.",
        "adv_objectives": [
            "Determine effects of varying parameter entries",
            "Connect eigenvalue changes to behavioral changes",
            "Interpret model sensitivity",
        ],
    },
    "LT24": {
        "title": "Linear Systems of Differential Equations",
        "type": "Two-Part",
        "f_description": "Express systems in matrix-vector form and find solutions.",
        "f_objectives": [
            "Express systems in matrix-vector form",
            "Verify vector-valued function solutions",
            "Apply eigenvalue/eigenvector method",
        ],
        "adv_description": "Analyze behavior of linear systems.",
        "adv_objectives": [
            "Write general solutions as linear combinations",
            "Reason about long-run behavior",
            "Classify equilibrium points",
        ],
    },
    "LT25": {
        "title": "Nonlinear Systems of Differential Equations",
        "type": "Group",
        "f_description": "Demonstrate understanding of phase-plane method for analyzing nonlinear systems.",
        "f_objectives": [
            "Understand phase plane meaning",
            "Interpret trajectories",
            "Sketch nullclines",
            "Recognize equilibrium points",
            "Identify time derivative signs",
            "Construct phase portraits",
            "Analyze long-term behavior",
        ],
        "notes": "Group assessment during Week 15 combining graphical and analytical methods.",
    },
}


def main():
    credentials_path = os.path.expanduser(os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", ""))
    sheet_id = os.environ.get("MATH141B_COURSE_CONFIG_ID", "")

    if not credentials_path or not sheet_id:
        print("Error: Set GOOGLE_SERVICE_ACCOUNT_FILE and MATH141B_COURSE_CONFIG_ID environment variables")
        return

    credentials = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(sheet_id)

    # Check if Learning Targets worksheet exists
    try:
        worksheet = spreadsheet.worksheet("Learning Targets")
        print("Found existing Learning Targets worksheet")
    except gspread.exceptions.WorksheetNotFound:
        print("Creating Learning Targets worksheet...")
        worksheet = spreadsheet.add_worksheet(title="Learning Targets", rows=30, cols=10)

    # Clear existing data and set up headers
    print("Setting up worksheet structure...")
    headers = ["LT_ID", "Type", "Title", "Description", "F_Description", "F_Objectives", "Adv_Description", "Adv_Objectives", "Notes"]

    # Clear and set headers
    worksheet.clear()
    worksheet.update('A1:I1', [headers])

    # Prepare all data rows
    rows = []
    for lt_id in sorted(LT_DETAILS.keys(), key=lambda x: int(x.replace("LT", ""))):
        details = LT_DETAILS[lt_id]

        # Create simple description from f_description
        description = details.get("f_description", "")

        # Format objectives as newline-separated strings
        f_objectives = "\n".join(details.get("f_objectives", []))
        adv_objectives = "\n".join(details.get("adv_objectives", []))

        row = [
            lt_id,
            details.get("type", "Two-Part"),
            details.get("title", ""),
            description,
            details.get("f_description", ""),
            f_objectives,
            details.get("adv_description", ""),
            adv_objectives,
            details.get("notes", ""),
        ]
        rows.append(row)
        print(f"  Prepared {lt_id}: {details.get('title', 'Unknown')}")

    # Batch update all rows
    print(f"\nWriting {len(rows)} learning targets to sheet...")
    worksheet.update(f'A2:I{len(rows)+1}', rows)

    print("Done!")


if __name__ == "__main__":
    main()
