import re
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import ast
from scipy.cluster.hierarchy import linkage, dendrogram
from statistics import mean 

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

def count_subjects(df_students,df_subjects):
    subjectNameVSS = dict()
    subjectCountVSS = dict()
    subjectNameUNI = dict()
    subjectCountUNI = dict()

    subjectName =  df_subjects.groupby(['subject_id']).apply(lambda x: x['subject_name'].to_string(index=False)).to_dict()
    
    for el in subjectName:
        if el[:3] == "632":
            subjectNameUNI[el]=subjectName[el]
            subjectCountUNI[el]=0
        elif el[:3] == "637":
            subjectNameVSS[el]=subjectName[el]
            subjectCountVSS[el]=0

    for index, row in df_students.drop(columns=['student_id']).iterrows():
        for el in row:
            if isinstance(el,str):
                predmeti = el[1:-1].split(',')
                for predmet in predmeti:
                    predmet = predmet.replace("\'","")
                    predmet = predmet.replace(" ","")
                    if subjectNameVSS.get(predmet):
                        subjectCountVSS[predmet]+=1
                    if subjectNameUNI.get(predmet):
                        subjectCountUNI[predmet]+=1
    
    return subjectNameVSS,subjectCountVSS,subjectNameUNI,subjectCountUNI

def draw_stevilo_vpisov_predmeti(df_students,df_subjects):

    subjectName =  df_subjects.groupby(['subject_id']).apply(lambda x: x['subject_name'].to_string(index=False)).to_dict()

    subjectNameVSS,subjectCountVSS,subjectNameUNI,subjectCountUNI = count_subjects(df_students,df_subjects)

    st.markdown(f"## Stevilo vpisov na predmete 2019-2024")

    #inicializiramo slovarje za hranjenje imen ter hranjenje stevila vpisov
    for el in subjectName:
        if el[:3] == "632":
            subjectNameUNI[el]=subjectName[el]
            subjectCountUNI[el]=0
        elif el[:3] == "637":
            subjectNameVSS[el]=subjectName[el]
            subjectCountVSS[el]=0

    #parsamo cez tabelo studentov in pregledamo vse predmete ki jih imajo ter nato pristejemo korektnim slovarjem
    for index, row in df_students.drop(columns=['student_id']).iterrows():
        for el in row:
            if isinstance(el,str):
                predmeti = el[1:-1].split(',')
                for predmet in predmeti:
                    predmet = predmet.replace("\'","")
                    predmet = predmet.replace(" ","")
                    if subjectNameVSS.get(predmet):
                        subjectCountVSS[predmet]+=1
                    if subjectNameUNI.get(predmet):
                        subjectCountUNI[predmet]+=1

    subjectFilterNameVSS = dict()
    subjectFilterCountVSS = dict()
    subjectFilterNameUNI = dict()
    subjectFilterCountUNI = dict()

    #gremo cez oba slovarja ter enostavno odstanimo tiste ki imajo manj kot 10 vpisov
    for el in subjectName:
        if el[:3] == "637" and subjectCountVSS[el]>=10:
            subjectFilterNameVSS[el]=subjectName[el]
            subjectFilterCountVSS[el]=subjectCountVSS[el]
        elif el[:3] == "632" and subjectCountUNI[el]>=10:
            subjectFilterNameUNI[el]=subjectName[el]
            subjectFilterCountUNI[el]=subjectCountUNI[el]

    arrsubjectCountUNI, arrsubjectNameUNI = zip(*sorted(zip(list(subjectFilterCountUNI.values()), list(subjectFilterNameUNI.values())),reverse=True))
    arrsubjectCountVSS, arrsubjectNameVSS = zip(*sorted(zip(list(subjectFilterCountVSS.values()), list(subjectFilterNameVSS.values())),reverse=True))

    #izpisemo vse s pomcojo dveh horizontalnih bargrafov. Ne se jih takoj navelicat ker teh je kar nekaj
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### UNI")
        plt.figure(figsize=(10, 12))
        plt.title('Stevilo vpisov na vsak predmet pri programu UNI')
        plt.barh(range(len(arrsubjectCountUNI)), arrsubjectCountUNI, align='center')
        plt.yticks(range(len(arrsubjectCountUNI)), arrsubjectNameUNI)
        ax = plt.gca()
        ax.set_xlim([0, 1600])
        st.pyplot(plt.gcf())

    with col2:
        st.markdown("#### VSS")
        plt.figure(figsize=(10, 12))
        plt.title('Stevilo vpisov na vsak predmet pri programu VSS')
        plt.barh(range(len(arrsubjectCountVSS)), arrsubjectCountVSS, align='center')
        plt.yticks(range(len(arrsubjectCountVSS)), arrsubjectNameVSS)
        ax = plt.gca()
        ax.set_xlim([0, 1600])
        st.pyplot(plt.gcf())

def count_student(df_students):

    studentCount = dict()
    studentCountVSS = dict()
    studentCountUNI = dict()

    for i in range(19,25):
        studentCount[str(i)+"/"+str(i+1)]=0
        studentCountVSS[str(i)+"/"+str(i+1)]=0
        studentCountUNI[str(i)+"/"+str(i+1)]=0

    for index, row in df_students.drop(columns=['student_id']).iterrows():
        for i in range(19,25):
            if row[str(i)+"/"+str(i+1)+"_1"] !="[]":
                prg = ""
                if not isinstance(row[str(i)+"/"+str(i+1)+"_1"],float):
                    prg = row[str(i)+"/"+str(i+1)+"_1"][2:5]
                if prg=="637" or prg=="632":
                    studentCount[str(i)+"/"+str(i+1)]+=1
                    if prg=="637":
                        studentCountVSS[str(i)+"/"+str(i+1)]+=1
                    else :
                        studentCountUNI[str(i)+"/"+str(i+1)]+=1
                break
    return studentCount,studentCountVSS,studentCountUNI

def draw_stevilo_vpisov_studenti(df_students):

    studentCount,studentCountVSS,studentCountUNI = count_student(df_students)

    st.markdown("## Stevilo vpisov v 1. letnik 2019-2024")
    plt.figure(figsize=(18, 4))
    plt.subplot(1,3,1)
    plt.title("Stevilo novih vpisov v 1. letnik program UNI in VSS")
    plt.xlabel("Leto")
    plt.ylabel("Stevilo studentov")
    plt.bar(studentCount.keys(), studentCount.values())
    plt.subplot(1,3,2)
    ax = plt.gca()
    ax.set_ylim([0, 400])
    plt.title("Stevilo novih vpisov v 1. letnik program UNI")
    plt.xlabel("Leto")
    plt.bar(studentCountUNI.keys(), studentCountUNI.values())
    plt.subplot(1,3,3)
    ax = plt.gca()
    ax.set_ylim([0, 400])
    plt.title("Stevilo novih vpisov v 1. letnik program VSS")
    plt.xlabel("Leto")
    plt.bar(studentCountVSS.keys(), studentCountVSS.values())
    st.pyplot(plt.gcf())

def draw_vpis_samo_1(df_students):

    studentCount1 = dict()
    studentCountVSS1 = dict()
    studentCountUNI1 = dict()
    for i in range(19,24):
        studentCount1[str(i)+"/"+str(i+1)]=0
        studentCountVSS1[str(i)+"/"+str(i+1)]=0
        studentCountUNI1[str(i)+"/"+str(i+1)]=0


    for index, row in df_students.iterrows():
        i = int(str(row['student_id'])[2:4])
        check = True
        for j in range(i+1,25):
            if isinstance(row[str(j)+"/"+str(j+1)+"_1"],str) or  isinstance(row[str(j)+"/"+str(j+1)+"_2"],str):
                check = False
                break
        if check and i<=23:
            if isinstance(row[str(i)+"/"+str(i+1)+"_1"],str):
                prg = row[str(i)+"/"+str(i+1)+"_1"][2:5]
                if prg=="637" or prg=="632":
                    studentCount1[str(i)+"/"+str(i+1)]+=1
                    if prg=="632":
                        studentCountUNI1[str(i)+"/"+str(i+1)]+=1
                    else:
                        studentCountVSS1[str(i)+"/"+str(i+1)]+=1

    st.markdown("## Stevilo studentov ki se je vpisalo samo v 1. letnik 2019-2023")
    plt.figure(figsize=(18, 4))
    plt.subplot(1,3,1)
    ax = plt.gca()
    ax.set_ylim([0, 120])
    plt.title("Stevilo studentov ki se je vpisalo samo v 1. letnik UNI in VSS")
    plt.xlabel("Leto")
    plt.ylabel("Stevilo studentov")
    plt.bar(studentCount1.keys(), studentCount1.values())
    plt.subplot(1,3,2)
    ax = plt.gca()
    ax.set_ylim([0, 120])
    plt.title("Stevilo studentov ki se je vpisalo samo v 1. letnik UNI")
    plt.xlabel("Leto")
    plt.bar(studentCountUNI1.keys(), studentCountUNI1.values())
    plt.subplot(1,3,3)
    ax = plt.gca()
    ax.set_ylim([0, 120])
    plt.title("Stevilo studentov ki se je vpisalo samo v 1. letnik VSS")
    plt.xlabel("Leto")
    plt.bar(studentCountVSS1.keys(), studentCountVSS1.values())
    st.pyplot(plt.gcf())

    studentCountDist = dict()
    studentCountDistUNI = dict()
    studentCountDisVSS = dict()
    studentCount,studentCountVSS,studentCountUNI = count_student(df_students)

    for year in studentCount1:
        studentCountDist[year]=studentCount1[year]/max(1,studentCount[year])*100
        studentCountDistUNI[year]=studentCountUNI1[year]/max(1,studentCountUNI[year])*100
        studentCountDisVSS[year]=studentCountVSS1[year]/max(1,studentCountVSS[year])*100

    st.markdown("## Delez studentov ki se je vpisalo samo v 1. letnik 2019-2023")
    plt.figure(figsize=(18, 4))
    plt.subplot(1,3,1)
    plt.title("Delez studentov ki se je vpisalo samo v 1. letnik UNI in VSS")
    plt.xlabel("Leto")
    plt.ylabel("Delez")
    ax = plt.gca()
    ax.set_ylim([0, 40])
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.bar(studentCountDist.keys(), studentCountDist.values())
    plt.subplot(1,3,2)
    plt.title("Delez studentov ki se je vpisalo samo v 1. letnik UNI")
    plt.xlabel("Leto")
    ax = plt.gca()
    ax.set_ylim([0, 40])
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.bar(studentCountDistUNI.keys(), studentCountDistUNI.values())
    plt.subplot(1,3,3)
    plt.title("Delez studentov ki se je vpisalo samo v 1. letnik VSS")
    plt.xlabel("Leto")
    ax = plt.gca()
    ax.set_ylim([0, 40])
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.bar(studentCountDisVSS.keys(), studentCountDisVSS.values())
    st.pyplot(plt.gcf())

def draw_ponovni_vpisi_predemti(df_students,df_subjects):
    subjectName =  df_subjects.groupby(['subject_id']).apply(lambda x: x['subject_name'].to_string(index=False)).to_dict()
    subjectNameVSS = dict()
    subjectPonVSS = dict()
    subjectNameUNI = dict()
    subjectPonUNI = dict()

    subjectNameVSS,subjectCountVSS,subjectNameUNI,subjectCountUNI = count_subjects(df_students,df_subjects)

    for el in subjectName:
        if el[:3] == "632" and subjectCountUNI[el]>=10:
            subjectNameUNI[el]=subjectName[el]
            subjectPonUNI[el]=0
        elif el[:3] == "637" and subjectCountVSS[el]>=10:
            subjectNameVSS[el]=subjectName[el]
            subjectPonVSS[el]=0
    
    subjectFilterNameVSS = dict()
    subjectFilterCountVSS = dict()
    subjectFilterNameUNI = dict()
    subjectFilterCountUNI = dict()

    #gremo cez oba slovarja ter enostavno odstanimo tiste ki imajo manj kot 10 vpisov
    for el in subjectName:
        if el[:3] == "637" and subjectCountVSS[el]>=10:
            subjectFilterNameVSS[el]=subjectName[el]
            subjectFilterCountVSS[el]=subjectCountVSS[el]
        elif el[:3] == "632" and subjectCountUNI[el]>=10:
            subjectFilterNameUNI[el]=subjectName[el]
            subjectFilterCountUNI[el]=subjectCountUNI[el]

    #enako kot prej gremo cez studente samo da tokrat hranimo od vsakega studenta zgodovino predmetov
    #v primeru da naletimo na predmet ki ga student ze ima v zgodovini, vemo da predmet ponavlja
    for index, row in df_students.drop(columns=['student_id']).iterrows():
        predmethist=set()
        for el in row:
            if isinstance(el,str):
                predmeti = el[1:-1].split(',')
                for predmet in predmeti:
                    predmet = predmet.replace("\'","")
                    predmet = predmet.replace(" ","")
                    if predmet in predmethist:
                        #tukaj uporabimo filtrirane predmete iz prejsnega grafa saj podatki ki imajo manj kot 10 vpisov nebi veliko pomenili
                        if subjectFilterNameVSS.get(predmet):
                            subjectPonVSS[predmet]+=1
                        if subjectFilterNameUNI.get(predmet):
                            subjectPonUNI[predmet]+=1
                    else:
                        predmethist.add(predmet)
                
    st.markdown("## Stevilo ponovnih vpisov na predmete 2019-2024")
    arrsubjectPonUNI, arrsubjectNameUNI = zip(*sorted(zip(list(subjectPonUNI.values()), list(subjectFilterNameUNI.values())),reverse=True))
    arrsubjectPonVSS, arrsubjectNameVSS = zip(*sorted(zip(list(subjectPonVSS.values()), list(subjectFilterNameVSS.values())),reverse=True))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### UNI")
        plt.figure(figsize=(10, 12))
        plt.title('Stevilo ponovnih vpisov na predmet UNI')
        ax = plt.gca()
        ax.set_xlim([0, 450])
        plt.barh(range(len(arrsubjectPonUNI)), arrsubjectPonUNI, align='center')
        plt.yticks(range(len(arrsubjectPonUNI)), arrsubjectNameUNI)
        st.pyplot(plt.gcf())
    with col2:
        st.markdown("#### VSS")
        plt.figure(figsize=(10, 12))
        ax = plt.gca()
        ax.set_xlim([0, 450])
        plt.title('Stevilo ponovnih vpisov na predmet VSS')
        plt.barh(range(len(arrsubjectPonVSS)), arrsubjectPonVSS, align='center')
        plt.yticks(range(len(arrsubjectPonVSS)), arrsubjectNameVSS)
        st.pyplot(plt.gcf())

    subjectDistUNI = dict()
    subjectDistVSS = dict()

    #delimo stevilo ponovitev s celotnim stevilom vpisov
    for subject in subjectFilterNameUNI:
        subjectDistUNI[subject]=subjectPonUNI[subject]/max(1,subjectCountUNI[subject])*100
    for subject in subjectFilterNameVSS:
        subjectDistVSS[subject]=subjectPonVSS[subject]/max(1,subjectCountVSS[subject])*100

    arrsubjectDistUNI, arrsubjectNameUNI = zip(*sorted(zip(list(subjectDistUNI.values()), list(subjectFilterNameUNI.values())),reverse=True))
    arrsubjectDistVSS, arrsubjectNameVSS = zip(*sorted(zip(list(subjectDistVSS.values()), list(subjectFilterNameVSS.values())),reverse=True))

    st.markdown("## Delez ponovnih vpisov na predmete 2019-2024")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### UNI")
        plt.figure(figsize=(10, 12))
        plt.title('Delez ponavljalcev na UNI')
        plt.barh(range(len(arrsubjectDistUNI)), arrsubjectDistUNI, align='center')
        plt.yticks(range(len(arrsubjectDistUNI)), arrsubjectNameUNI)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mtick.PercentFormatter())
        ax.set_xlim([0, 50])
        st.pyplot(plt.gcf())
    with col2:
        st.markdown("#### VSS")
        plt.figure(figsize=(10, 12))
        plt.title('Delez ponavljalcev na VSS')
        plt.barh(range(len(arrsubjectDistVSS)), arrsubjectDistVSS, align='center')
        plt.yticks(range(len(arrsubjectDistVSS)), arrsubjectNameVSS)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mtick.PercentFormatter())
        ax.set_xlim([0, 50])
        st.pyplot(plt.gcf())

def subject_viewer(df_students,df_subjects):

    st.markdown("## Zgodovina predmetov")

    subjectName =  df_subjects.groupby(['subject_id']).apply(lambda x: x['subject_name'].to_string(index=False)).to_dict()
    subjectFilterName = dict()
    subjectNameCode = dict()
    subjectNameVSS,subjectCountVSS,subjectNameUNI,subjectCountUNI = count_subjects(df_students,df_subjects)


    for el in subjectName:
        oznaka = ""
        if el[:3] == "637":
            oznaka = " (VSS)"
        elif el[:3] == "632":
            oznaka = " (UNI)"
        else:
            continue

        if ((subjectCountVSS.get(el) and subjectCountVSS[el] >= 10) or
            (subjectCountUNI.get(el) and subjectCountUNI[el] >= 10)):
            ime_z_oznako = subjectName[el] + oznaka
            subjectFilterName[el] = ime_z_oznako
            subjectNameCode[ime_z_oznako] = el

    option = st.selectbox(
        'Izberi predmet',
        subjectFilterName.values())


    st.write('izbrani predmet: ', option,'sifra: ',subjectNameCode[option])

    #spremenu SubjectCode na poljubno sifro in dobi rezultate
    SubjectCode = subjectNameCode[option]
    PonHist = dict()
    TotalVpis = dict()
    Delez = dict()

    for i in range(19,25):
        PonHist[str(i)+"/"+str(i+1)]=0
        TotalVpis[str(i)+"/"+str(i+1)]=0

    #ne izmumljam kolesa na novo parsanje dokaj podobno prejsnim
    for index, row in df_students.drop(columns=['student_id']).iterrows():
        predmethist=set()
        for i in range(19,25):
            for j in range(1,3):
                if not isinstance(row[str(i)+"/"+str(i+1)+"_"+str(j)],float):
                    predmeti = row[str(i)+"/"+str(i+1)+"_"+str(j)][1:-1].split(',')
                    for predmet in predmeti:
                        predmet = predmet.replace("\'","")
                        predmet = predmet.replace(" ","")
                        if predmet==SubjectCode:
                            if predmet in predmethist:
                                PonHist[str(i)+"/"+str(i+1)]+=1
                            
                            TotalVpis[str(i)+"/"+str(i+1)]+=1

                        predmethist.add(predmet)

    #izbrisemo podatke za leto 2019/2020 saj ceprav vemo stevilo vpisov v 1. letnik ne moremo izvedeti podatkov za ponavljanje
    del PonHist["19/20"]
    del TotalVpis["19/20"]

    #priravimo se dealez ponavljalcev za leto
    for el in PonHist:
        Delez[el]=PonHist[el]/max(TotalVpis[el],1)*100


    plt.figure(figsize=(12, 4))
    plt.subplot(1,2,1)
    plt.title("Vsi vpisi na predmet "+subjectName[SubjectCode])
    plt.xlabel("Leto")
    plt.ylabel("Stevilo studentov")
    plt.bar(TotalVpis.keys(), TotalVpis.values(), label="novi vpisi")
    plt.bar(PonHist.keys(), PonHist.values(), bottom=0, color='red',label="ponavljalci")
    plt.legend(loc="upper left")
    plt.subplot(1,2,2)
    plt.title("Delez studentov ki ponavlja "+subjectName[SubjectCode])
    plt.xlabel("Leto")
    plt.ylabel("Delez studentov ki ponavlja")
    ax = plt.gca()
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.bar(Delez.keys(), Delez.values(),color="red")
    st.pyplot(plt.gcf())

def subjectPassRateAvg(SubjectCode,df_students):
    PonHist = dict()
    TotalVpis = dict()
    Delez = dict()

    for i in range(19,25):
        PonHist[str(i)+"/"+str(i+1)]=0
        TotalVpis[str(i)+"/"+str(i+1)]=0

    for index, row in df_students.drop(columns=['student_id']).iterrows():
        predmethist=set()
        for i in range(19,25):
            for j in range(1,3):
                if not isinstance(row[str(i)+"/"+str(i+1)+"_"+str(j)],float):
                    predmeti = row[str(i)+"/"+str(i+1)+"_"+str(j)][1:-1].split(',')
                    for predmet in predmeti:
                        predmet = predmet.replace("\'","")
                        predmet = predmet.replace(" ","")
                        if predmet==SubjectCode:
                            if predmet in predmethist:
                                PonHist[str(i)+"/"+str(i+1)]+=1
                            
                            TotalVpis[str(i)+"/"+str(i+1)]+=1

                        predmethist.add(predmet)

    del PonHist["19/20"]
    del TotalVpis["19/20"]

    for el in PonHist:
        Delez[el]=PonHist[el]/max(TotalVpis[el],1)

    return round(mean(Delez.values()),2)

def subjectPassRateLast(SubjectCode,df_students):
    PonHist = dict()
    TotalVpis = dict()
    Delez = dict()

    for i in range(19,25):
        PonHist[str(i)+"/"+str(i+1)]=0
        TotalVpis[str(i)+"/"+str(i+1)]=0

    for index, row in df_students.drop(columns=['student_id']).iterrows():
        predmethist=set()
        for i in range(19,25):
            for j in range(1,3):
                if not isinstance(row[str(i)+"/"+str(i+1)+"_"+str(j)],float):
                    predmeti = row[str(i)+"/"+str(i+1)+"_"+str(j)][1:-1].split(',')
                    for predmet in predmeti:
                        predmet = predmet.replace("\'","")
                        predmet = predmet.replace(" ","")
                        if predmet==SubjectCode:
                            if predmet in predmethist:
                                PonHist[str(i)+"/"+str(i+1)]+=1
                            
                            TotalVpis[str(i)+"/"+str(i+1)]+=1

                        predmethist.add(predmet)

    del PonHist["19/20"]
    del TotalVpis["19/20"]

    for el in PonHist:
        Delez[el]=PonHist[el]/max(TotalVpis[el],1)

    return round(next(reversed(Delez.values())),2)

def kalkulator_sanse(df_students, df_subjects):
    st.markdown("## Kalkulator sanse")
    subjectName = df_subjects.groupby(['subject_id']).apply(lambda x: x['subject_name'].to_string(index=False)).to_dict()
    subjectFilterName = dict()
    subjectNameCode = dict()
    subjectNameVSS, subjectCountVSS, subjectNameUNI, subjectCountUNI = count_subjects(df_students, df_subjects)

    for el in subjectName:
        oznaka = ""
        if el[:3] == "637":
            oznaka = " (VSS)"
        elif el[:3] == "632":
            oznaka = " (UNI)"
        else:
            continue

        if ((subjectCountVSS.get(el) and subjectCountVSS[el] >= 10) or
            (subjectCountUNI.get(el) and subjectCountUNI[el] >= 10)):
            ime_z_oznako = subjectName[el] + oznaka
            subjectFilterName[el] = ime_z_oznako
            subjectNameCode[ime_z_oznako] = el

    # Multiselect za izbiro predmetov
    selected_subjects = st.multiselect(
        "Izberi predmete:",
        options=list(subjectFilterName.values()),
        default=[],
        key="multiselect_predmeti"
    )

    # Gumb za izračun
    if st.button("Izračunaj"):
        if selected_subjects:
            subjectCodes = [subjectNameCode[subj] for subj in selected_subjects]
            sa = [subjectPassRateAvg(subject, df_students) for subject in subjectCodes]
            sl = [subjectPassRateLast(subject, df_students) for subject in subjectCodes]

            passChanceAvg = 1
            passChancelast = 1

            for i in range(len(sa)):
                passChanceAvg = round(passChanceAvg * (1 - sa[i]), 2)
                passChancelast = round(passChancelast * (1 - sl[i]), 2)

            st.write("Sansa da naredis letnik z izbranimi predmeti glede na povprecje: " + str(passChanceAvg * 100) + "%")
            st.write("Sansa da naredis letnik z izbranimi predmeti glede na zadnje leto: " + str(passChancelast * 100) + "%")
        else:
            st.info("Izberi vsaj en predmet.")


def zgodovina_studenta(df_students, df_subjects):
    st.markdown("## Zgodovina študenta")

    df_students_id = df_students[['student_id']].copy()
    valid_options = df_students_id['student_id'].astype(str).tolist()

    option = st.selectbox('Izberi vpisno številko:', valid_options)

    if st.button("Postalkaj vpisno"):
        selected_student_id = int(option)

        selected_student_row = df_students[df_students['student_id'] == selected_student_id]
        
        if selected_student_row.empty:
            st.write("No data found for the selected student ID.")
            return

        selected_student_row = selected_student_row.iloc[0]

        student_subjects = {}

        for column in selected_student_row.index:
            if column == 'student_id':
                continue

            cell_value = selected_student_row[column]
            if isinstance(cell_value, str):
                try:
                    subject_ids = ast.literal_eval(cell_value)
                except (ValueError, SyntaxError):
                    subject_ids = []
            else:
                subject_ids = []

            subjects = []

            for sub_id in subject_ids:
                if str(sub_id)[2:3] == '5':
                    continue
                subject_name = df_subjects.loc[df_subjects['subject_id'] == sub_id, 'subject_name'].values
                subject_program = 'UNI' if str(sub_id)[2:3] == '2' else 'VSS'
                if subject_name.size > 0:
                    subjects.append(f"{subject_name[0]} ({subject_program})")
                else:
                    subjects.append(f"{sub_id} (zaradi nekega razloga ni imena)")

            if subjects:
                student_subjects[column] = subjects


        for key, subjects in student_subjects.items():
            year, semester = key.split('_')
            st.write(f"Leta {year} v {semester}. semestru, je študent/ka z vpisno številko {selected_student_id} imel/a naslednje predmete:")
            for subject in subjects:
                st.write(f"- {subject}")
            # zakomentirana opcija izpise vse v eni vrstici. manj za scrollat, also manj berljivo
            #subjects_line = ", ".join(subjects)
            #st.write(f"Leta {year} v {semester} semestru, je študent/ka z vpisno številko {selected_student_id} imel/a naslednje predmete:\n- {subjects_line}")


# Naloži podatke
df = pd.read_csv("students_final.csv")
subjects = pd.read_csv("subjects_3.csv")
subject_info = subjects[~subjects['student_year'].astype(str).str.contains("ni vnosov")]

#prikaze zgodovino poljubnega predmeta
subject_viewer(df.copy(),subject_info.copy())

#kalkulira sanso da naredis letnik glede na izbrane premdete
kalkulator_sanse(df.copy(),subject_info.copy())

# zgodovina studenta
zgodovina_studenta(df.copy(), subjects.copy())

# Izriši analizo za oba programa
draw_heatmap_dendrogram(df.copy(), subject_info.copy(), 'VSS')
draw_heatmap_dendrogram(df.copy(), subject_info.copy(), 'UNI')

#izpise stevilo vpisov po letih
draw_stevilo_vpisov_studenti(df.copy())

#izpise vse ki so se vpisali samo za 1 leto
draw_vpis_samo_1(df.copy())

#izpise totalne vpise na predmete
draw_stevilo_vpisov_predmeti(df.copy(),subject_info.copy())

#izpise statistiko ponavljanja predmetov
draw_ponovni_vpisi_predemti(df.copy(),subject_info.copy())
