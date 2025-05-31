import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import ast
from scipy.cluster.hierarchy import linkage, dendrogram

# Nastavitve strani
st.set_page_config(page_title="Analiza urnika FRI", layout="wide")
st.title("Analiza urnika FRI")

# Funkcija za izris heatmap + dendrogram
def draw_heatmap_dendrogram(df, subject_info, program_label):
    st.markdown(f"## {program_label} predmeti")

    subjects = subject_info[subject_info['subject_program'] == program_label]
    subject_name_map = dict(zip(subjects['subject_id'], subjects['subject_name']))
    subject_ids = set(subjects['subject_id'])

    all_subjects = df.drop(columns=["student_id"]).applymap(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )
    combined_subjects = all_subjects.apply(lambda row: set(sum(row.dropna().tolist(), [])), axis=1)
    filtered_subjects = combined_subjects.apply(lambda s: s & subject_ids)

    df["all_subjects"] = filtered_subjects
    all_subject_ids = sorted(set().union(*df["all_subjects"]))

    subject_matrix = pd.DataFrame(0, index=df.index, columns=all_subject_ids)
    for i, subjects in enumerate(df["all_subjects"]):
        subject_matrix.loc[i, list(subjects)] = 1

    subject_matrix.columns = [subject_name_map.get(subj_id, subj_id) for subj_id in subject_matrix.columns]
    correlation_matrix = subject_matrix.corr()
    distance_matrix = 1 - correlation_matrix
    linked = linkage(distance_matrix, method='average')

    # Postavitev: dva stolpca
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Korelacijska matrika")
        fig1, ax1 = plt.subplots(figsize=(12, 10))
        sns.heatmap(correlation_matrix, cmap="coolwarm", center=0, ax=ax1)
        ax1.set_title(f"Korelacija med {program_label} predmeti")
        st.pyplot(fig1)

    with col2:
        st.markdown("#### Dendrogram")
        fig2, ax2 = plt.subplots(figsize=(14, 6))
        dendrogram(linked, labels=correlation_matrix.columns, leaf_rotation=90, ax=ax2)
        ax2.set_title(f"Dendrogram {program_label} predmetov")
        st.pyplot(fig2)

# Naloži podatke
df = pd.read_csv("students_final.csv")
subject_info = pd.read_csv("subjects_3.csv")
subject_info = subject_info[~subject_info['student_year'].astype(str).str.contains("ni vnosov")]

# Izriši analizo za oba programa
draw_heatmap_dendrogram(df.copy(), subject_info.copy(), 'VSS')
draw_heatmap_dendrogram(df.copy(), subject_info.copy(), 'UNI')
