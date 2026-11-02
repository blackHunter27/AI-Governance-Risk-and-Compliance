"""Standalone figures for the TechHire synthetic fairness assessment."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.metrics import GROUP_ORDER

PRIMARY = "#164e63"
SECONDARY = "#13a89e"
WARNING = "#d97745"
RED = "#b94d60"
BG = "#f4f7fb"


def style(ax):
    ax.set_facecolor("white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dce4ea", lw=0.8, alpha=0.8)
    ax.set_axisbelow(True)


def save(fig, output, name):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / name, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate_figures(data: pd.DataFrame, metrics: pd.DataFrame,
                     summary: pd.DataFrame, output: str | Path) -> list[str]:
    generated = []
    # 1. Selection-rate gap and four-fifths threshold, three panels
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.7), sharey=True)
    for ax, (attr, labels) in zip(axes, GROUP_ORDER.items()):
        base = metrics.loc[(metrics.attribute == attr) & (metrics.scenario == "Baseline")].set_index("group").loc[labels]
        mitigated = metrics.loc[(metrics.attribute == attr) & (metrics.scenario == "Mitigated")].set_index("group").loc[labels]
        x = np.arange(len(labels)); width = .36
        ax.bar(x-width/2, base.selection_rate*100, width, color=RED, label="Biased baseline")
        ax.bar(x+width/2, mitigated.selection_rate*100, width, color=SECONDARY, label="Mitigated rule")
        for i, (v1, v2) in enumerate(zip(base.selection_rate, mitigated.selection_rate)):
            ax.text(i-width/2, v1*100+.7, f"{v1:.1%}", ha="center", fontsize=8, color=RED)
            ax.text(i+width/2, v2*100+.7, f"{v2:.1%}", ha="center", fontsize=8, color=PRIMARY)
        ax.set_xticks(x, labels, rotation=18, ha="right"); ax.set_ylim(0, 55)
        ax.set_title(attr.replace("_", " ").title(), weight="bold"); style(ax)
    axes[0].set_ylabel("Applicants selected (%)")
    axes[-1].legend(loc="upper right", fontsize=9)
    fig.suptitle("TechHire | Selection rates by demographic group", fontsize=16, weight="bold")
    fig.tight_layout(rect=(0, .04, 1, .92))
    save(fig, output, "01_selection_rates.png"); generated.append("01_selection_rates.png")

    # 2. TPR / FPR by group and scenario
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    labels_all = []
    for attr, groups in GROUP_ORDER.items():
        labels_all += [f"{attr.split('_')[0]}: {g}" for g in groups]
    baseline = metrics[metrics.scenario == "Baseline"]
    mitigation = metrics[metrics.scenario == "Mitigated"]
    for ax, metric, title in zip(axes,["tpr","fpr"],["True positive rate (qualified applicants)","False positive rate (unqualified applicants)"]):
        x=np.arange(len(baseline)); w=.38
        ax.barh(x-w/2, baseline[metric]*100, w, color=RED, label="Biased baseline")
        ax.barh(x+w/2, mitigation[metric]*100, w, color=SECONDARY, label="Mitigated rule")
        ax.set_yticks(x,labels_all,fontsize=8);ax.invert_yaxis();ax.set_xlim(0,100)
        ax.set_title(title,weight="bold");ax.grid(axis="x", alpha=.18);ax.spines[["top","right"]].set_visible(False)
    axes[-1].legend(loc="lower right")
    fig.suptitle("TechHire | Equalized-odds components",weight="bold",fontsize=16)
    fig.tight_layout(rect=(0,.03,1,.94))
    save(fig,output,"02_equalized_odds_components.png");generated.append("02_equalized_odds_components.png")

    # 3. Intersectionality heatmap (gender x nationality)
    fig,axes=plt.subplots(1,2,figsize=(12.5,5.1))
    genders=list(GROUP_ORDER['gender']); countries=list(GROUP_ORDER['nationality_group'])
    heat=[]
    for scenario,ax in zip(["baseline_selected","mitigated_selected"],axes):
        matrix=np.zeros((len(genders),len(countries)))
        counts=np.zeros_like(matrix,dtype=int)
        for i,g in enumerate(genders):
            for j,c in enumerate(countries):
                sample=data[(data.gender==g)&(data.nationality_group==c)]
                matrix[i,j]=sample[scenario].mean()*100
                counts[i,j]=len(sample)
        im=ax.imshow(matrix,cmap="YlGnBu",vmin=10,vmax=55)
        ax.set_xticks(range(len(countries)),countries);ax.set_yticks(range(len(genders)),genders)
        ax.set_title("Biased baseline" if scenario=="baseline_selected" else "Mitigated rule",weight="bold")
        for i in range(len(genders)):
            for j in range(len(countries)):
                ax.text(j,i,f"{matrix[i,j]:.1f}%\n(n={counts[i,j]})",ha="center",va="center",fontsize=10,
                        color="white" if matrix[i,j]>35 else "#173345",weight="bold")
    fig.colorbar(im,ax=axes.ravel().tolist(),label="Selection rate (%)",shrink=.8)
    fig.suptitle("Intersectional selection rates | Gender × nationality",fontsize=15,weight="bold")
    fig.subplots_adjust(top=.82,bottom=.10,right=.86,wspace=.22)
    save(fig,output,"03_intersectional_heatmap.png");generated.append("03_intersectional_heatmap.png")

    # 4. Group disparity changes
    fig,axes=plt.subplots(1,2,figsize=(14.5,5.4))
    for ax,metric,title in zip(axes,["selection_rate_gap_pp","equalized_odds_gap_pp"],
                               ["Selection-rate gap","Equalized-odds gap (max of TPR/FPR gaps)"]):
        arr=summary.pivot(index="attribute",columns="scenario",values=metric).loc[list(GROUP_ORDER)]
        x=np.arange(len(arr));w=.35
        ax.bar(x-w/2,arr["Baseline"],w,color=RED,label="Biased baseline")
        ax.bar(x+w/2,arr["Mitigated"],w,color=SECONDARY,label="Mitigated rule")
        ax.set_xticks(x,[a.replace("_"," ").title() for a in arr.index]);ax.set_ylabel("Difference (percentage points)")
        ax.set_title(title,weight="bold");style(ax)
        ax.legend(loc="upper right")
    fig.suptitle("Fairness gap analysis | Equal review capacity",fontsize=16,weight="bold")
    fig.tight_layout(rect=(0,.04,1,.94))
    save(fig,output,"04_mitigation_comparison.png");generated.append("04_mitigation_comparison.png")

    # 5. Executive dashboard: snapshot with clear assumptions
    fig=plt.figure(figsize=(14.7,7.4),facecolor=BG)
    gs=fig.add_gridspec(2,3,height_ratios=[.70,1.5],hspace=.25,wspace=.23)
    n=len(data); baseline=int(data.baseline_selected.sum()); after=int(data.mitigated_selected.sum())
    metrics_snapshot=[(f"{n:,}","applicant records"),(f"{baseline:,} / {n:,}","baseline selections"),(f"{after:,} / {n:,}","mitigated selections")]
    for i,(v,label) in enumerate(metrics_snapshot):
        ax=fig.add_subplot(gs[0,i]);ax.set_facecolor("white");ax.axis("off")
        ax.text(.05,.65,v,transform=ax.transAxes,fontsize=27,color=PRIMARY,weight="bold")
        ax.text(.05,.32,label,transform=ax.transAxes,fontsize=12,color="#516375")
    ax=fig.add_subplot(gs[1,:]); ax.set_facecolor("white")
    pivot=summary.pivot(index="attribute",columns="scenario",values="min_selection_ratio").loc[list(GROUP_ORDER)]
    x=np.arange(len(pivot));w=.34
    ax.bar(x-w/2,pivot["Baseline"],w,color=RED,label="Biased baseline")
    ax.bar(x+w/2,pivot["Mitigated"],w,color=SECONDARY,label="Mitigated rule")
    ax.axhline(.8,color=WARNING,linestyle="--",lw=1.7,label="Four-fifths screening reference")
    for j,(v0,v1) in enumerate(zip(pivot["Baseline"],pivot["Mitigated"])):
        ax.text(j-w/2,v0+.017,f"{v0:.2f}",ha="center",fontsize=10)
        ax.text(j+w/2,v1+.017,f"{v1:.2f}",ha="center",fontsize=10)
    ax.set_xticks(x,[t.replace("_"," ").title() for t in pivot.index]);ax.set_ylim(0,1.17)
    ax.set_ylabel("Minimum selection-rate ratio to highest group");ax.legend(loc="upper left",fontsize=9)
    ax.set_title("Minimum selection-rate ratio across demographic groups",weight="bold",pad=18);style(ax)
    fig.suptitle("TECHHIRE | RECRUITMENT FAIRNESS ANALYSIS",fontsize=19,weight="bold",x=.05,ha="left",y=.98,color="#113b50")
    save(fig,output,"05_executive_fairness_dashboard.png");generated.append("05_executive_fairness_dashboard.png")
    return generated
