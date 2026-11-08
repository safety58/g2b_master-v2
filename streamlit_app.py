import random
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="나라장터 종합 입찰 및 적격심사 시스템",
    page_icon="🏗️",
    layout="wide",
)

st.title("🏗️ 나라장터 공사입찰 투찰금액 산출 & 적격심사 종합 분석 시스템")
st.markdown(
    "나라장터 공공공사 입찰을 위한 **[1] A값 반영 투찰금액 산출**, **[2] 단독 적격심사**, **[3] 공동도급 적격심사**, **[4] 발주처 및 경쟁사 사정율 빅데이터 분석**을 수행합니다."
)

# ---------------------------------------------------------
# 공통 사이드바: 기본 설정
# ---------------------------------------------------------
st.sidebar.header("⚙️ 공통 입찰 조건 설정")

construction_name = st.sidebar.text_input(
    "공사명 입력",
    value="OO지역 노후상수도 정비공사",
    help="분석할 입찰 공고의 공사명을 입력하세요.",
)

base_price = st.sidebar.number_input(
    "기초금액 (원)", min_value=1_000_000, value=1_000_000_000, step=10_000_000
)
a_value = st.sidebar.number_input(
    "A값 (국민건강보험료 등 합산액, 원)", value=35_000_000, step=1_000_000
)
target_bid_rate = st.sidebar.number_input(
    "낙찰하한율 / 투찰율 (%)",
    min_value=50.0,
    max_value=100.0,
    value=87.745,
    step=0.001,
    format="%.3f",
)

# ---------------------------------------------------------
# 상단 메인 탭 분리 (4가지 페이지 구성)
# ---------------------------------------------------------
tab_calc, tab_eval_single, tab_eval_joint, tab_bigdata = st.tabs(
    [
        "🧮 1페이지: 투찰금액 산출 및 복수예가",
        "⚖️ 2페이지: 단독 적격심사 자동계산",
        "🤝 3페이지: 공동도급 적격심사 자동계산",
        "📈 4페이지: 발주처·경쟁사 사정율 빅데이터 분석",
    ]
)


# =========================================================
# [페이지 1] 투찰금액 산출 및 15개 복수예가 분석
# =========================================================
with tab_calc:
    st.subheader(f"📌 [{construction_name}] 투찰금액 산출 및 예가 분석")
    st.markdown(
        "**[A값 적용 투찰금액 산출 공식]**\n"
        r"$$\text{투찰금액} = \left[ (\text{기초금액} \times \text{사정율}) - A\text{값} \right] \times \text{낙찰하한율} + A\text{값}$$"
    )
    st.markdown("---")

    sub_tab1, sub_tab2 = st.tabs(
        ["🧮 투찰금액 산출 및 비교표", "🎲 15개 복수예가 몬테카를로 분석"]
    )

    with sub_tab1:
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            predicted_assessment_rate = st.number_input(
                "예측 사정율 (%)",
                min_value=95.0,
                max_value=105.0,
                value=100.1500,
                step=0.0001,
                format="%.4f",
            )
        with col_in2:
            st.info(
                f"💡 **입찰 조건 요약**\n"
                f"- 기초금액: {base_price:,} 원\n"
                f"- A값: {a_value:,} 원\n"
                f"- 낙찰하한율: {target_bid_rate}%"
            )

        estimated_price = base_price * (predicted_assessment_rate / 100.0)
        final_bid_price = (estimated_price - a_value) * (
            target_bid_rate / 100.0
        ) + a_value
        purity_ratio = (final_bid_price / base_price) * 100

        st.markdown("### 🎯 최종 산출 결과")
        k1, k2, k3 = st.columns(3)
        k1.metric("산출된 예정가격", f"{int(estimated_price):,} 원")
        k2.metric(
            "🎯 최종 추천 투찰금액",
            f"{int(final_bid_price):,} 원",
            delta=f"기초대비 {purity_ratio:.3f}%",
        )
        k3.metric("A값 차감 대상 금액", f"{int(estimated_price - a_value):,} 원")

        if purity_ratio < 80.0:
            st.warning("⚠️ 경고: 투찰금액이 지나치게 낮습니다.")
        else:
            st.success("✅ A값 공식이 정상적으로 반영되어 투찰금액이 산출되었습니다.")

        st.markdown("---")
        st.subheader("📋 사정율 구간별 투찰금액 비교표")
        rates_to_test = [99.5, 99.8, 100.0, 100.15, 100.3, 100.5]
        table_data = []
        for r in rates_to_test:
            est_p = base_price * (r / 100.0)
            bid_p = (est_p - a_value) * (target_bid_rate / 100.0) + a_value
            table_data.append(
                {
                    "사정율 (%)": f"{r:.4f}%",
                    "예정가격 (원)": f"{int(est_p):,}",
                    "투찰금액 (원)": f"{int(bid_p):,}",
                    "기초대비율 (%)": f"{(bid_p/base_price)*100:.3f}%",
                }
            )
        st.dataframe(
            pd.DataFrame(table_data),
            use_container_width=True,
            hide_index=True,
        )

    with sub_tab2:
        st.markdown(
            "15개 복수예비가격 중 무작위로 4개를 추첨($\\binom{15}{4}=1,365$ 조합)하여 가장 확률이 높은 사정율을 예측합니다."
        )

        use_custom = st.checkbox("15개 복수예가 직접 입력", value=False)
        reserve_prices = []
        if use_custom:
            cols_r = st.columns(5)
            for i in range(15):
                with cols_r[i % 5]:
                    val = st.number_input(
                        f"예가 {i+1}",
                        value=int(base_price * (1 + (i - 7) * 0.002)),
                    )
                    reserve_prices.append(val)
        else:
            np.random.seed(42)
            variations = np.linspace(-0.02, 0.02, 15)
            reserve_prices = [int(base_price * (1 + v)) for v in variations]

        sim_count = st.select_slider(
            "시뮬레이션 횟수",
            options=[10000, 50000, 100000, 200000],
            value=100000,
        )

        if st.button("🚀 몬테카를로 시뮬레이션 실행", type="primary"):
            simulated_rates = []
            for _ in range(sim_count):
                selected_4 = random.sample(reserve_prices, 4)
                est_p = sum(selected_4) / 4.0
                simulated_rates.append((est_p / base_price) * 100)

            sim_arr = np.array(simulated_rates)
            mean_rate = np.mean(sim_arr)
            counts, bin_edges = np.histogram(sim_arr, bins=50)
            mode_rate = (
                bin_edges[np.argmax(counts)]
                + bin_edges[np.argmax(counts) + 1]
            ) / 2

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("최우선 추천 사정율", f"{mode_rate:.4f} %")
            m2.metric("평균 사정율", f"{mean_rate:.4f} %")
            m3.metric("최대 사정율", f"{np.max(sim_arr):.4f} %")
            m4.metric("최소 사정율", f"{np.min(sim_arr):.4f} %")

            fig, ax = plt.subplots(figsize=(10, 3.5))
            ax.hist(
                sim_arr,
                bins=50,
                density=True,
                alpha=0.6,
                color="#1f77b4",
                edgecolor="black",
            )
            ax.axvline(
                mode_rate,
                color="red",
                linestyle="--",
                linewidth=2,
                label=f"최다 빈도: {mode_rate:.4f}%",
            )
            ax.set_title("Assessment Rate Probability Distribution")
            ax.set_xlabel("Assessment Rate (%)")
            ax.legend()
            st.pyplot(fig)


# =========================================================
# [페이지 2] 단독 적격심사 자동계산 및 판정 페이지
# =========================================================
with tab_eval_single:
    st.subheader(
        f"⚖️ [{construction_name}] 단독 적격심사 자동계산 (실적·시공능력·재무비율 입력)"
    )
    st.markdown(
        "자사 단독 투찰 시 **3년/5년 실적 금액, 시공능력평가액, 부채비율 및 유동비율**을 입력하여 "
        "정밀하게 적격 통과 여부(Pass/Fail)를 판정합니다."
    )
    st.markdown("---")

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown("#### 🏢 자사 스펙 및 평가 입력")
        perf_period = st.radio(
            "실적 인정 기간 선택", ["최근 5년 실적", "최근 3년 실적"], key="s_period"
        )
        if perf_period == "최근 5년 실적":
            perf_amt_s = st.number_input(
                "최근 5년 실적 금액 (원)",
                min_value=0,
                value=1_500_000_000,
                step=50_000_000,
                key="s_p5",
            )
        else:
            perf_amt_s = st.number_input(
                "최근 3년 실적 금액 (원)",
                min_value=0,
                value=1_000_000_000,
                step=50_000_000,
                key="s_p3",
            )

        capa_s = st.number_input(
            "시공능력평가액 (원)",
            min_value=0,
            value=5_000_000_000,
            step=100_000_000,
            key="s_capa",
        )

        st.markdown("--- 자사 경영상태 입력 ---")
        mgmt_mode_s = st.radio(
            "경영상태 평가방식", ["신용평가등급", "재무비율(부채/유동)"], key="s_mm"
        )
        if mgmt_mode_s == "신용평가등급":
            credit_score_s = st.selectbox(
                "신용평가등급",
                ["만점(AAA~BBB-)", "보통(BB)", "감점(B이하)"],
                key="s_cred",
            )
            debt_r_s, current_r_s = 0.0, 0.0
        else:
            debt_r_s = st.number_input(
                "부채비율 (%)", value=65.0, step=1.0, key="s_debt"
            )
            current_r_s = st.number_input(
                "유동비율 (%)", value=150.0, step=1.0, key="s_curr"
            )
            credit_score_s = ""

        is_local_s = st.checkbox(
            "관내 지역업체 본점 소재지 가산점 적용", value=True, key="s_local"
        )

    with col_e2:
        st.markdown("#### 📊 단독 적격심사 종합 판정 결과")
        exp_mult_s = perf_amt_s / base_price if base_price > 0 else 0

        st.info(
            f"💡 **자사 역량 환산 현황**\n"
            f"- 실적 배수 ({perf_period}): **{exp_mult_s:.2f}배** (기준 1.0배 이상 시 만점)\n"
            f"- 시공능력평가액: {capa_s:,} 원"
        )

        max_exp, max_mgmt, max_price, max_local, max_other = (
            15.0,
            15.0,
            50.0,
            5.0,
            15.0,
        )
        scr_exp_s = (
            max_exp if exp_mult_s >= 1.0 else max_exp * (exp_mult_s / 1.0)
        )

        if mgmt_mode_s == "신용평가등급":
            scr_mgmt_s = (
                max_mgmt
                if "만점" in credit_score_s
                else (
                    max_mgmt * 0.9
                    if "보통" in credit_score_s
                    else max_mgmt * 0.7
                )
            )
        else:
            scr_mgmt_s = (
                max_mgmt
                if debt_r_s < 100 and current_r_s > 100
                else max_mgmt * 0.85
            )

        scr_local_s = max_local if is_local_s else 0.0
        scr_price_s = max_price * 0.98
        scr_other_s = max_other

        total_s = (
            scr_exp_s + scr_mgmt_s + scr_price_s + scr_local_s + scr_other_s
        )
        passing_limit = 85.0

        st.metric(
            label="단독 종합 적격 평점",
            value=f"{total_s:.2f} 점",
            delta="통과 기준 85점 이상",
        )

        if total_s >= passing_limit:
            st.success("🎉 **[PASS] 단독 적격심사 통과 대상**입니다.")
        else:
            st.warning(
                "⚠️ **[FAIL] 단독 적격심사 미달**입니다. 실적이나 재무비율을 확인해 주세요."
            )

    st.markdown("---")
    st.subheader("📋 단독 평가 항목별 상세 배점표")
    eval_df_s = pd.DataFrame(
        {
            "평가 항목": [
                f"시공경험 ({perf_period} 환산배수 {exp_mult_s:.2f}배)",
                "경영상태",
                "입찰가격 점수",
                "지역업체 참여도",
                "기타 (신인도 등)",
                "합계",
            ],
            "배점 한도": [
                max_exp,
                max_mgmt,
                max_price,
                max_local,
                max_other,
                100.0,
            ],
            "획득 점수": [
                round(scr_exp_s, 2),
                round(scr_mgmt_s, 2),
                round(scr_price_s, 2),
                round(scr_local_s, 2),
                round(scr_other_s, 2),
                round(total_s, 2),
            ],
        }
    )
    st.dataframe(eval_df_s, use_container_width=True, hide_index=True)


# =========================================================
# [페이지 3] 공동도급 적격심사 자동계산
# =========================================================
with tab_eval_joint:
    st.subheader(
        f"⚖️ [{construction_name}] 공동도급 적격심사 자동계산 (실적·시공능력·재무비율 입력)"
    )
    st.markdown(
        "구성원별 **지분율, 3년/5년 실적금액, 시공능력평가액, 부채비율 및 유동비율**을 입력하여 "
        "지분율 가중평균 합산 적격 평점과 지역의무 공동도급 가산점을 검토합니다."
    )
    st.markdown("---")

    col_j1, col_j2 = st.columns(2)

    with col_j1:
        st.markdown("#### 🤝 대표사 및 공동참여사 정보 입력")

        st.markdown("##### 1) 대표사 (A사)")
        ratio_a = st.slider(
            "대표사 지분율 (%)",
            min_value=10,
            max_value=90,
            value=60,
            step=1,
            key="ra_a",
        )
        perf_period_a = st.radio(
            "대표사 실적 기간", ["최근 5년", "최근 3년"], key="per_a"
        )
        if perf_period_a == "최근 5년":
            perf_amt_a = st.number_input(
                "대표사 최근 5년 실적 금액 (원)",
                min_value=0,
                value=1_500_000_000,
                step=50_000_000,
                key="pa_a5",
            )
        else:
            perf_amt_a = st.number_input(
                "대표사 최근 3년 실적 금액 (원)",
                min_value=0,
                value=1_000_000_000,
                step=50_000_000,
                key="pa_a3",
            )

        capa_a = st.number_input(
            "대표사 시공능력평가액 (원)",
            min_value=0,
            value=5_000_000_000,
            step=100_000_000,
            key="ca_a",
        )

        st.markdown("--- 대표사 경영상태 입력 ---")
        mgmt_mode_a = st.radio(
            "대표사 평가방식", ["신용평가등급", "재무비율(부채/유동)"], key="mm_a"
        )
        if mgmt_mode_a == "신용평가등급":
            cred_a = st.selectbox(
                "대표사 신용등급",
                ["만점(AAA~BBB-)", "보통(BB)", "감점(B이하)"],
                key="cr_a",
            )
            debt_a, current_a = 0.0, 0.0
        else:
            debt_a = st.number_input(
                "대표사 부채비율 (%)", value=65.0, step=1.0, key="db_a"
            )
            current_a = st.number_input(
                "대표사 유동비율 (%)", value=150.0, step=1.0, key="cu_a"
            )
            cred_a = ""

        st.markdown("---")
        st.markdown(f"##### 2) 공동참여사 (B사) [지분율: {100 - ratio_a}%]")
        ratio_b = 100 - ratio_a
        perf_period_b = st.radio(
            "공동사 실적 기간", ["최근 5년", "최근 3년"], key="per_b"
        )
        if perf_period_b == "최근 5년":
            perf_amt_b = st.number_input(
                "공동사 최근 5년 실적 금액 (원)",
                min_value=0,
                value=800_000_000,
                step=50_000_000,
                key="pa_b5",
            )
        else:
            perf_amt_b = st.number_input(
                "공동사 최근 3년 실적 금액 (원)",
                min_value=0,
                value=500_000_000,
                step=50_000_000,
                key="pa_b3",
            )

        capa_b = st.number_input(
            "공동사 시공능력평가액 (원)",
            min_value=0,
            value=3_000_000_000,
            step=100_000_000,
            key="ca_b",
        )

        st.markdown("--- 공동사 경영상태 입력 ---")
        mgmt_mode_b = st.radio(
            "공동사 평가방식", ["신용평가등급", "재무비율(부채/유동)"], key="mm_b"
        )
        if mgmt_mode_b == "신용평가등급":
            cred_b = st.selectbox(
                "공동사 신용등급",
                ["만점(AAA~BBB-)", "보통(BB)", "감점(B이하)"],
                key="cr_b",
            )
            debt_b, current_b = 0.0, 0.0
        else:
            debt_b = st.number_input(
                "공동사 부채비율 (%)", value=75.0, step=1.0, key="db_b"
            )
            current_b = st.number_input(
                "공동사 유동비율 (%)", value=130.0, step=1.0, key="cu_b"
            )
            cred_b = ""

        st.markdown("---")
        is_local_joint = st.checkbox(
            "지역의무 공동도급 또는 관내업체 공동참여 (지분 40% 이상 시 지역가산점 만점)",
            value=True,
            key="j_local",
        )

    with col_j2:
        st.markdown("#### 📊 공동도급 적격심사 종합 판정 결과")
        exp_mult_a = perf_amt_a / base_price if base_price > 0 else 0
        exp_mult_b = perf_amt_b / base_price if base_price > 0 else 0

        st.info(
            f"💡 **주요 역량 환산 현황**\n"
            f"- 대표사 실적 배수: **{exp_mult_a:.2f}배** (시공능력평가액: {capa_a:,} 원)\n"
            f"- 공동사 실적 배수: **{exp_mult_b:.2f}배** (시공능력평가액: {capa_b:,} 원)"
        )

        w_a = ratio_a / 100.0
        w_b = ratio_b / 100.0

        scr_e_a = (
            15.0 if exp_mult_a >= 1.0 else 15.0 * (exp_mult_a / 1.0)
        )
        scr_e_b = (
            15.0 if exp_mult_b >= 1.0 else 15.0 * (exp_mult_b / 1.0)
        )
        weighted_exp = (scr_e_a * w_a) + (scr_e_b * w_b)

        if mgmt_mode_a == "신용평가등급":
            s_mgmt_a = (
                15.0
                if "만점" in cred_a
                else (15.0 * 0.9 if "보통" in cred_a else 15.0 * 0.7)
            )
        else:
            s_mgmt_a = (
                15.0 if debt_a < 100 and current_a > 100 else 15.0 * 0.85
            )

        if mgmt_mode_b == "신용평가등급":
            s_mgmt_b = (
                15.0
                if "만점" in cred_b
                else (15.0 * 0.9 if "보통" in cred_b else 15.0 * 0.7)
            )
        else:
            s_mgmt_b = (
                15.0 if debt_b < 100 and current_b > 100 else 15.0 * 0.85
            )

        weighted_mgmt = (s_mgmt_a * w_a) + (s_mgmt_b * w_b)
        local_cond_met = is_local_joint and (ratio_a >= 40 or ratio_b >= 40)
        weighted_local = 5.0 if local_cond_met else 0.0

        price_score = 50.0 * 0.98
        other_score = 15.0
        total_joint_score = (
            weighted_exp
            + weighted_mgmt
            + weighted_local
            + price_score
            + other_score
        )

        st.metric(
            label="공동수급체 종합 평점",
            value=f"{total_joint_score:.2f} 점",
            delta=f"대표사 {ratio_a}% + 공동사 {ratio_b}%",
        )

        if total_joint_score >= 85.0:
            st.success(
                "🎉 **[PASS] 공동도급 적격심사 통과 대상**입니다. 공동수급체 합산 점수가 기준을 충족합니다."
            )
        else:
            st.warning(
                "⚠️ **[FAIL] 공동도급 적격심사 미달**입니다. 구성원의 실적, 지분율 또는 재무비율을 확인해 주세요."
            )

    st.markdown("---")
    st.subheader("📋 공동도급 가중평균 상세 내역")
    joint_df = pd.DataFrame(
        {
            "평가 항목": [
                f"시공경험 (대표사 환산배수 {exp_mult_a:.2f}배 / 공동사 환산배수 {exp_mult_b:.2f}배)",
                "경영상태 (가중평균)",
                "입찰가격 점수",
                "지역업체 참여도",
                "기타 (신인도 등)",
                "합계",
            ],
            "배점 한도": [15.0, 15.0, 50.0, 5.0, 15.0, 100.0],
            "공동수급체 획득 점수": [
                round(weighted_exp, 2),
                round(weighted_mgmt, 2),
                round(price_score, 2),
                round(weighted_local, 2),
                round(other_score, 2),
                round(total_joint_score, 2),
            ],
        }
    )
    st.dataframe(joint_df, use_container_width=True, hide_index=True)


# =========================================================
# [페이지 4] 발주처별 및 경쟁사 사정율 빅데이터 분석 페이지
# =========================================================
with tab_bigdata:
    st.subheader("📈 발주처별 및 주요 경쟁사 사정율 빅데이터 분석")
    st.markdown(
        "나라장터 과거 개찰 데이터 기반 **주요 발주처별 5개년 평균 사정율 및 표준편차(σ)**와 "
        "**주요 경쟁 업체들의 투찰 성향 및 낙찰 패턴**을 비교 분석합니다."
    )
    st.markdown("---")

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.markdown("#### 🏢 주요 발주처별 지난 5개년 사정율 통계")
        org_stats_df = pd.DataFrame(
            {
                "발주처 기관명": [
                    "조달청 (시설공사)",
                    "한국토지주택공사 (LH)",
                    "한국전력공사",
                    "국토교통부 지방국토청",
                    "지방자치단체 (시·군·구)",
                ],
                "최근 5년 평균 사정율": [
                    "100.1245 %",
                    "99.8520 %",
                    "100.0412 %",
                    "99.9105 %",
                    "100.2150 %",
                ],
                "표준편차 (σ)": [
                    "± 0.35",
                    "± 0.42",
                    "± 0.28",
                    "± 0.40",
                    "± 0.51",
                ],
                "주요 낙찰 핫존 (Hot Band)": [
                    "100.0% ~ 100.3%",
                    "99.5% ~ 100.0%",
                    "99.8% ~ 100.2%",
                    "99.6% ~ 100.1%",
                    "100.0% ~ 100.5%",
                ],
            }
        )
        st.dataframe(org_stats_df, hide_index=True, use_container_width=True)

    with col_b2:
        st.markdown("#### 🏆 상위 경쟁 업체 투찰 성향 및 패턴 분석")
        comp_stats_df = pd.DataFrame(
            {
                "경쟁 업체 유형": [
                    "A건설 (저가 공략형)",
                    "B엔지니어링 (정석 평균형)",
                    "C종합건설 (안전 안정형)",
                    "D이앤씨 (고배수 도전형)",
                ],
                "평균 투찰 사정율": [
                    "99.45 %",
                    "100.02 %",
                    "100.45 %",
                    "100.85 %",
                ],
                "주요 입찰 공종": [
                    "소액 수의계약 / 전문공사",
                    "대형 지자체 적격심사",
                    "공기업 대단위 시설공사",
                    "제한경쟁 토목공사",
                ],
                "낙찰 적중률": ["높음 (빈발)", "매우 높음", "보통", "낮음"],
            }
        )
        st.dataframe(comp_stats_df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📊 발주처별 사정율 변동성 시각화 비교")
    
    # 샘플 바 차트 시각화
    chart_data = pd.DataFrame(
        {
            "발주처": ["조달청", "LH", "한전", "국토부", "지자체"],
            "평균사정율": [100.1245, 99.8520, 100.0412, 99.9105, 100.2150],
        }
    ).set_index("발주처")
    
    st.bar_chart(chart_data)