table_names = [
    "actual_payment", "bike_deliveries_first", "borrower", "collateral", "collateral_detailed",
    "expected_payment", "loan_payment", "loans", "master_contracts", "master_loans"
]

prefixed_table_names = [f"public.{name}" for name in table_names]

create_statements = [
    """
        CREATE TABLE public.actual_payment (    -- table description: "공유 플랫폼으로부터 실제로 수취한 월별 사용료와 관련 수수료 정보를 저장하는 테이블입니다. 각 계약(loan_id)별로 매월 발생하는 실제 수취 금액을 상세하게 기록하며, 원금(principal), 이자(interest), 세금(VAT), 기타 수수료, 할인 금액 등을 포함합니다."
            loan_id varchar(50) NOT NULL,       -- 각 대출을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합. A unique number/string for each loan.
            schedule_number int8 NOT NULL,      -- 동일한 loan_id(계약)에 대해 계약 기간 동안 매월 플랫폼으로부터 징수된 사용료의 회차를 나타내는 정수이다. 첫 번째 회차는 1부터 시작한다.
            loan_id_schedule varchar(50) NULL,  -- loan_id 와 schedule_number 를 하이픈(-)으로 결합하여 생성된 고유 문자열이다. (예: loan_id가 G-V-SM-2024003이고 schedule_number가 1이면 'G-V-SM-2024003-1'로 저장)
            actual_payment_date timestamp NULL, -- 플랫폼으로부터 월 사용료를 받은 실제 날짜를 YYYY-MM-DD 형식으로 저장.
            actual_principal float8 NULL,       -- 상환 스케줄에 따라 지급된 금액 중 일부를 저장하는 필드로, refinanced/restructured amounts/discounts, VAT은 포함하지 않는다. actual_interest 칼럼과 더하면 플랫폼으로부터 실제로 받은 해당 월 사용료(세금 제외)가 된다.
            actual_interest float8 NULL,        -- 상환 스케줄에 따라 지급된 금액 중 일부를 저장하는 필드로, refinanced/restructured amounts/discounts, VAT은 포함하지 않는다. actual_principal 칼럼과 더하면 플랫폼으로부터 실제로 받은 해당 월 사용료(세금 제외)가 된다.
            actual_other_fees float8 NULL,      -- 실제 지급된 기타 수수료를 저장하는 필드이다.
            actual_interest_vat float8 NULL,    -- 플랫폼으로부터 받은 사용료에 대한 세금. actual_principal 칼럼과 actual_interest 칼럼을 더한 뒤 0.11을 곱해서 구한다. 계산: (actual_principal + actual_interest) * 0.11
            "late_fee_&_other_charges" float8 NULL, -- 지연 납부시 발생한 연체료 및 기타 수수료의 총액을 저장하는 필드로, 연체 이자(late interest)와 기타 부대 비용이 모두 포함된다.
            discount_given_principal float8 NULL,   -- 조기 상환 시 이번 회차 또는 다음 회차 상환 원금에서 차감해 주는 할인 금액이다.
            discount_given_interests float8 NULL,   -- 조기 상환 시 이번 회차 또는 다음 회차 상환 이자에서 차감해 주는 할인 금액이다.
            discount_given_vat float8 NULL,         -- 조기 상환 시 이번 회차 또는 다음 회차 상환 세금에서 차감해 주는 할인 금액이다.
            refinanced_amount float8 NULL,
            recoverd_concept float8 NULL,
            recovered_principal float8 NULL,
            recovered_non_principal float8 NULL,
            CONSTRAINT actual_payment_pkey PRIMARY KEY (loan_id, schedule_number),
            CONSTRAINT fk_actual_payment_loan_id FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
        );
    """,

    """
    CREATE TABLE public.bike_deliveries_first ( -- table description: 계약 체결 후 첫 달 동안 분리 배송된 전기 바이크 단위로 운행과 수익 정보를 관리하는 테이블.
        introduction_id int8 NOT NULL,          -- 계약 체결 이후 첫 달 동안 발생한 각 분리 배송마다 순차적으로 부여한 일련번호이다. A sequential identifier (e.g., 1, 2, ...) for each distinct delivery shipment occurring within the first month of the contract.
        contract_id varchar(50) NULL,           -- 각 계약을 고유하게 식별하기 위해 사용된다. A unique identifier for each contract.
        loan_id varchar(50) NOT NULL,           -- 각 대출을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합. A unique number/string for each loan.
        daily_fee_include_vat int8 NULL,        -- 부가세를 포함한 일별 대여 요금이다. Daily rental fee including VAT.
        first_month_evs int8 NULL,              -- 계약 체결 이후 첫 달에 배송된 전기 바이크(ev) 대수이다.
        first_month_days int8 NULL,             -- 첫 달 배송 건에 포함된 각 전기 바이크가 해당 첫 달 동안 운행한 실제 일수.
        first_month_total_usage int8 NULL,      -- 첫 달에 배송된 전기 바이크(ev) 수와 운행 일수를 곱해 계산한 값이다. 계산: first_month_evs * first_month_days
        first_month_receivable int8 NULL,       -- 계약 체결 이후 첫 달에 예정되거나 실제로 수취된 총 금액으로 첫 달 운행 일수에 일별 요금(daily_fee_include_vat)을 곱해 산출한다. The total amount of money scheduled to be received or actually received. 계산: first_month_total_usage * daily_fee_include_vat
        first_month_tax int8 NULL,              -- 계약 체결 이후 첫 달에 발생한 세금의 총액이다. The amount of tax (likely VAT) associated with the charges or payments related to the first month of the contract. 계산: first_month_receivable * 11/111
        CONSTRAINT bike_deliveries_first_pkey PRIMARY KEY (introduction_id, loan_id),
        CONSTRAINT fk_bike_deliveries_first_loan_id FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
    );
    """,

    """
    CREATE TABLE public.borrower (          -- table description: 차용인, borrower에 대한 정보를 저장하는 테이블.
        borrower_id varchar(50) NOT NULL,   -- 차용인(개인 또는 법인)을 고유하게 식별하기 위해 부여되는 식별자이다. loans 테이블의 borrower_id 칼럼이 이 칼럼을 foreign key로 참조한다.
        company_name varchar(50) NULL,      -- 차용인이 기업인인인 경우에만 해당 기업의 공식 명칭을 저장하는 필드이다.
        gender float8 NULL,                 -- 차용인이 개인인 경우에만 성별을 나타내는 필드이다. 예: Male, Female, NA.
        "type" float8 NULL,                 -- 차용인이 개인인지, 기업인지 나타냐는 필드이다. 예: Person, Business.
        "birth/creation_year" float8 NULL,  -- 개인인 경우 출생 연도를, 기업인 경우 설립 연도를 YYYY 형식으로 저장한다.
        "income/revenues" float8 NULL,      -- 개인인 경우 연간 소득 수준을, 기업인 경우 연간 매출액을 저장하며 신용 정책에 활용한다.
        "industry/occupation" float8 NULL,  -- 개인인 경우 직업 분류를, 기업인 경우 산업/업종 분류를 저장한다.
        "number_of_dependents
    /employees" float8 NULL,                -- 개인인 경우 차용인에게 경제적으로 의존하는 부양가족의 수를, 기업의 경우 해당 기업의 직원 수를 저장하는 필드이다.
        education float8 NULL,              -- 개인인 경우에만 차용인의 학력 수준을 저장하는 필드이다.
        country varchar(50) NULL,           -- 개인인 경우 거주 국가를, 기업인 경우 사업장 소재 국가를 저장하는 필드이다.
        "state/province/city" varchar(50) NULL, -- 개인인 경우 거주 주/도/시 를, 기업인 경우 사업장 소재 주/도/시 를 저장하는 필드이다.
        settlement_type float8 NULL,        -- 거주지 및 사업 소재지가 농촌인지 도시인지 구별해 저장하는 필드이다.
        CONSTRAINT borrower_pkey PRIMARY KEY (borrower_id)
    );
    """,

    """
    CREATE TABLE public.collateral (        -- table description: 담보 자산에 대한 정보를 저장하는 테이블이다.
        collateral_id float8 NOT NULL,      -- 각 담보 자산을 고유하게 식별하기 위해 부여되는 식별자이다.
        loan_id varchar(50) NOT NULL,       -- 각 대출을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합이다.
        "type" varchar(50) NULL,            -- 담보 자산의 유형을 나타내는 필드이다. 예: 2W Electric Vehicle.
        category varchar(50) NULL,          -- 담보 자산의 세부 유형(예: 전기 바이크 모델)을 작성하는 필드이다.
        additional_information float8 NULL, -- 담보 자산에 대한 추가 정보를 기술하는 필드이다.
        appraisal_price float8 NULL,        -- 담보 자산의 평가 가격을 저장하는 필드이다. 전기 바이크(ev)의 cost_per_unit과 number_of_evs 를 곱한 뒤 세금을 제외하기 위해 1.11로 나눠준다.
        currency varchar(50) NULL,          -- 담보 자산의 평가 가격을 기록할 때 사용된 통화를 나타내는 필드이다.
        CONSTRAINT collateral_pkey PRIMARY KEY (collateral_id, loan_id),
        CONSTRAINT fk_collateral_loan_id FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
    );
    """,

    """
    CREATE TABLE public.collateral_detailed (   -- table description: 담보 자산에 대한 상세 정보(제조사 정보, 모델명 및 주행 데이터)를 저장하는 테이블이다.
        loan_id varchar(50) NULL,           -- 각 대출을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합이며, loans 테이블의 loan_id 칼럼을 참조하는 foreign key이다. A unique number/string for each loan.
        motorcycle_id varchar(50) NOT NULL, -- 각 담보물(오토바이)의 고유 식별자이다.
        delivery_date timestamp NULL,       -- 계약 당사자에게 담보(예 : 전기 자전거)의 배송이 시작된 날짜를 YYYY-MM-DD 형식으로 저장한다.
        oem_brand varchar(50) NULL,         -- 담보물의 OEM 제조사 브랜드 이름을 저장하는 필드이다.
        model_name varchar(50) NULL,        -- 담보물의 OEM 제조사 제품 라인 내에서 사용되는 특정 모델 명칭을 저장하는 필드이다.
        mobility_platform varchar(50) NULL, -- 담보물의 데이터와 서비스(공유 플랫폼이므로 전기 바이크 대여 서비스)를 관리하는 플랫폼 이름을 저장하는 필드이다. The platform used to manage collateral data and services.
        avg_speed float8 NULL,              -- 담보물이 특정 기간이나 특정 거리 동안 이동한 평균 속도를 저장하는 필드이다. The average speed of the collateral calculated over a specified period or distance.
        total_mileage float8 NULL,          -- 담보물의 최초 사용 시점 또는 마지막 초기화 시점 이후 누적해서 주행한 총 거리를 저장하는 필드이다. The cumulative distance traveled by the collateral since its first use or last reset
        total_trip float8 NULL,             -- 담보물이 수행한 개별 이동 횟수의 총합을 저장하는 필드이다. The total number of individual journeys or trips made by the collateral.
        CONSTRAINT collateral_detailed_pkey PRIMARY KEY (motorcycle_id),
        CONSTRAINT fk_collateral_detailed_loan_id FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
    );
    """,

    """
    CREATE TABLE public.expected_payment (  -- table description: 공유 플랫폼으로부터 예정된 월별 사용료와 관련 수수료 정보를 저장하는 테이블입니다. 각 계약(loan_id)별로 매월 발생할 것으로 예상되는 수취 금액을 상세하게 기록하며, 원금(principal), 이자(interest), 세금(VAT), 기타 수수료 등을 포함합니다. 이 테이블은 계약 체결 시점에 정해진 상환 스케줄을 기반으로 작성된 예상 데이터이다.
        loan_id varchar(50) NOT NULL,       -- 각 대출을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합. A unique number/string for each loan.
        schedule_number int8 NOT NULL,      -- 동일한 loan_id(계약)에 대해 계약 기간 동안 매월 플랫폼으로부터 징수된 사용료의 회차를 나타내는 정수이다. 첫 번째 회차는 1부터 시작한다.
        loan_id_schedule varchar(50) NULL,  -- loan_id 와 schedule_number 를 하이픈(-)으로 결합하여 생성된 고유 문자열이다. (예: loan_id가 G-V-SM-2024003이고 schedule_number가 1이면 'G-V-SM-2024003-1'로 저장)
        delivery_date timestamp NULL,       -- 계약 당사자에게 담보(예: 자전거)의 배송이 시작된 날짜를 YYYY-MM-DD 형식으로 저장한다.
        actual_payment_date timestamp NULL, -- 플랫폼으로부터 월 사용료를 받은 실제 날짜를 YYYY-MM-DD 형식으로 저장.
        scheduled_installment_date timestamp NULL,  -- 사전에 플랫폼으로부터 매월 사용료를 받기로 정한 날짜를 YYYY-MM-DD 형식으로 저장.
        past_due float8 NULL,               -- actual_payment_date 칼럼과 scheduled_installment_date 칼럼 사이의 차이를 일(day) 단위로 저장함. (actual_payment_date가 2024-11-12 이고 scheduled_installment_date가 2024-11-7이라면 past_due는 7이다.) 계산: EXTRACT(DAY FROM (actual_payment_date - scheduled_installment_date))
        scheduled_principal float8 NULL,    -- 플랫폼으로부터 받은 사용료의 일부. scheduled_interest 칼럼과 더하면 플랫폼으로부터 받은 해당 월 사용료(세금 제외)가 된다.
        scheduled_interest float8 NULL,     -- 플랫폼으로부터 받은 사용료의 일부. scheduled_principal 칼럼과 더하면 플랫폼으로부터 받은 해당 월 사용료(세금 제외)가 된다.
        scheduled_other_fees float8 NULL,   -- 플랫폼으로부터 받을 기타 수수료.
        scheduled_tax float8 NULL,          -- 플랫폼으로부터 받은 사용료에 대한 세금. scheduled_principal 칼럼과 scheduled_interest 칼럼을 더한 뒤 0.11을 곱해서 구한다. 계산: (scheduled_principal + scheduled_interest) * 0.11
        CONSTRAINT expected_payment_pkey PRIMARY KEY (loan_id, schedule_number),
        CONSTRAINT fk_expected_payment_loan_id FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
    );
    """,

    """
    CREATE TABLE public.loan_payment (      -- table description: 각 대출 계약(loan_id)에 대해 회차별 상환 스케줄과 실제 상환 현황을 관리하는 테이블
        loan_id varchar(50) NOT NULL,       -- 각 대출을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합. A unique number/string for each loan.
        schedule_no int8 NOT NULL,          -- 동일한 대출(loan_id)에 대해 반복되는 상환 일정의 각 회차를 식별하기 위해 부여되는 번호이다.
        bank varchar(50) NULL,              -- 대출(loan)을 제공하는 은행의 이름을 저장하는 필드이다.
        bank_loan_code varchar(50) NOT NULL,    -- 은행에서 대출 상품을 식별하기 위해 내부적으로 사용하는 코드이다.
        payment_schedule timestamp NULL,    -- 각 상환 회차별로 정기 상환금(installment)을 은행에 납부하기로 예정된 날짜를 YYYY-MM-DD 형식으로 저장하는 필드이다.
        principal int8 NULL,                -- 각 상환 회차별로 은행에 납부할 예정인 원금 금액을 저장하는 필드이다.
        interest int8 NULL,                 -- 각 상환 회차별로 은행에 납부할 예정인 이자 금액을 저장하는 필드이다.
        total int8 NULL,                    -- 각 상환 회차별로 납부할 원금과 이자를 합산한 총 상환 예정 금액을 저장하는 필드이다.
        actual_payment_date timestamp NULL,     -- 실제 납부가 이루어진 날짜를 YYYY-MM-DD 형식으로 저장하는 필드이다.
        dpd float8 NULL,                    -- 지불 예정일(payment_schedule)부터 실제 지불일(actual_payment_date)까지 경과된 일수를 저장하는 필드이다.
        actual_principal int8 NULL,         -- 각 상환 회차별로 실제 납부된 원금 금액을 저장하는 필드로, refinanced/restructured amounts/discounts, VAT은 포함하지 않는다.
        actual_interest int8 NULL,          -- 각 상환 회차별로 실제 납부된 이자 금액을 저장하는 필드로, refinanced/restructured amounts/discounts, VAT은 포함하지 않는다.
        actual_total int8 NULL,             -- 각 상환 회차별로 실제 납부된 원금(actual_principal)과 이자(actual_interest)를 합산한 총액을 저장하는 필드이다.
        CONSTRAINT loan_payment_pkey PRIMARY KEY (loan_id, schedule_no, bank_loan_code),
        CONSTRAINT fk_loan_payment_loan_id FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
    );
    """,

    """
    CREATE TABLE public.loans (             -- table description: 전기 바이크 공유 플랫폼과의 대여 계약 정보를 저장하는 테이블이다. 이 테이블의 'loan'은 은행 대출이 아닌, 전기 바이크를 공유 플랫폼에 대여해주는 계약을 의미한다. master_loan 테이블의 'loan'은 은행과의 대출 계약을 의미하므로, 두 테이블의 'loan' 개념을 구분하여 사용해야 한다. 이 테이블은 대여 계약의 기본 정보, 차용인 정보, 대여 조건 등을 포함한다.
        borrower_id varchar(50) NULL,       -- 차용인(개인 또는 법인)을 고유하게 식별하기 위해 부여되는 식별자이다. borrower 테이블에 반드시 존재하는 foreign key 이다. A unique number/string for borrower(person/entity)
        loan_id varchar(50) NOT NULL,       -- 각 대출을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합. A unique number/string for each loan.
        product_type varchar(50) NULL,      -- 어떤 고객 유형을 대상으로 하는지 구분하는 텍스트 필드이다. (예: B2B 등) The type of product.
        loan_grade float8 NULL,             -- 대출의 신용·위험 등급을 알파벳으로 구분하여 저장하는 필드이다. The loan risk grade (eg. A, B, C, etc.)
        credit_bureau_score float8 NULL,    -- 대여 신청을 할 때 borrower의 신용점수를 저장하는 필드이다. Credit bureau score of a borrower when the application is submitted.
        internal_score float8 NULL,         -- 파트너의 신용, 위험을 평가하기 위해 내부적으로 산출한 고유 점수이다. Value of the propetary score of the partner.
        loan_amount float8 NULL,            -- master_contracts 테이블의 cost_per_unit 칼럼과 number_of_evs 칼럼을 곱해 산출한 대출 금액이며, origination_fee는 포함되지만 기타 추가 수수료는 제외된다. The loan amount (Including origination fee charged to the client but without other fees).
        currency varchar(50) NULL,          -- 대출 금액에 사용된 통화를 나타내는 필드이다. (예 : IDR) Currency of the amount lended.
        origination_fee int8 NULL,          -- 대출 금액(loan_amount)에 포함되는 수수료로, 고객에게 부과되는 수수료이다. Fees charged to the client and included in the loan amount.
        disbursement_date timestamp NULL,
        effective_interest_rate float8 NULL,    -- 계약의 연수익률로, 데이터베이스 상에서는 소수(decimal) 형태로 저장된다. The effective interest rate.
        term int8 NULL,                     -- 렌탈 계약의 기간을 저장하는 필드이다. The term of loan.
        term_unit varchar(50) NULL,         -- 렌탈 계약 기간의 단위를 나타내는 필드이다. Y는 연, M은 월, D는 일을 의미한다. The unit used to measure the term. Y for years, D for Days or M for months.
        loan_type varchar(50) NULL,         -- 렌탈 계약의 상환 방식 유형을 나타내는 필드이다. Bullet, Bullet w/ Periodic Interest, Flat, Amortizing의 네 가지 값 중 하나로 구분된다. Type of schedule of the loan: Bullet, Bullet w/ Periodic Interest, Flat, Amortizing.
        loannumber int8 NULL,               -- 플랫폼을 통해 체결한 총 계약 건수를 나타내는 필드이다. Number of loan that the borrower took with the platform.
        originator_agent float8 NULL,       -- 고객에게 계약을 중개한 기관 이름을 저장하는 필드이다. Name of the originator agent.
        lender varchar(50) NULL,
        loan_use varchar(50) NULL,
        restructure_from_loan_id varchar(50) NULL,
        restructure_to_loan_id varchar(50) NULL,
        refinanced_from_loan_id varchar(50) NULL,
        refinanced_to_loan_id varchar(50) NULL,
        CONSTRAINT loans_pkey PRIMARY KEY (loan_id),
        CONSTRAINT fk_loans_borrower_id FOREIGN KEY (borrower_id) REFERENCES public.borrower(borrower_id)
    );
    """,

    """
    CREATE TABLE public.master_contracts (      -- table description: 전체 계약에 대한 정보
        contract_id varchar(50) NOT NULL,       -- 각 계약을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합이다. A unique number/string for each contract.
        loan_id varchar(50) NULL,               -- 각 대출을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합. A unique number/string for each loan.
        sn int8 NOT NULL,                       -- 각 레코드를 고유하게 식별하기 위해 부여되는 일련번호이다. A unique number/string for each loan.
        contract_date timestamp NULL,           -- 계약이 실제로 집행된 날짜를 YYYY-MM-DD 형식의 문자열로 저장한다. The date of contract disbursement in YYYY-MM-DD format.
        contract_party varchar(50) NULL,        -- 차용인을 고유하게 식별하기 위해 부여되는 고유 식별자이다. A unique number/string for borrower - person/entity.
        ev_brand varchar(50) NULL,              -- 전기 바이크 브랜드 이름을 나타내는 텍스트 필드이다. Electric vehicle brand name.
        term int8 NULL,                         -- 계약의 기간을 개월 단위로 저장하는 필드이다. Contract duration in months.
        daily_fee_exclude_vat float8 NULL,      -- 부가세를 제외한 일별 대여 요금이다. Daily rental fee excluding VAT. 계산: daily_fee_include_vat / 1.11
        number_of_evs int8 NULL,                -- 해당 계약에 포함된 전기 바이크의 총 대수이다. Number of electric vehicles in the contract.
        cost_per_unit int8 NULL,                -- 전기 바이크 한 대 가격이다.
        days int8 NULL,                         -- 계약의 총 대여 일수. Total number of rental days. 계산: term / 12 * 365
        daily_fee_include_vat int8 NULL,        -- 부가세를 포함한 일별 대여 요금. Daily rental fee including VAT.
        total_receivable_exclude_vat int8 NULL,     -- 부가세를 제외한 계약 건별 총 수취 금액. Total receivable amount excluding VAT. 계산: ROUND(total_receivable_include_vat / 1.11, 2)
        total_receivable_include_vat int8 NULL,     -- 부가세를 포함한 계약 건별 총 수취 금액. Total receivable amount including VAT. 계산: total_receivable_include_vat / days / number_of_evs
        total_principal float8 NULL,            -- 계약서에 명시된 총 원금 금액. The total principal amount specified in the contract. 계산: ROUND(number_of_evs * cost_per_unit / 1.11, 2)
        total_vat float8 NULL,                  -- 계약 건별 부가세 총액. The total amount of Value Added Tax applicable to the entire contract value. 계산: total_receivable_include_vat - total_receivable_exclude_vat
        effective_return float8 NULL,           -- 대출 또는 계약을 통해 실제로 실현된 유효 수익률(소수 형태). The calculated effective rate of return realized from the loan or contract.
        batch int8 NULL,                        -- 계약과 연계된 배송이 계약 체결 후 첫 달 동안 여러 번에 걸쳐 분할 출고되었는지를 나타내는 불리언 플래그이다. 값이 1인 경우 첫 달 동안 여러 번에 걸쳐 분할 출고되었고, 값이 0인 경우 한 번에 모두 출고되었다. A flag indicating whether the delivery associated with the contract occurred in multiple separate shipments during the first month.
        CONSTRAINT master_contracts_pkey PRIMARY KEY (contract_id, sn),
        CONSTRAINT fk_master_contracts_loan_id FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
    );
    """,

    """
    CREATE TABLE public.master_loans (      -- table description: 은행과의 대출 계약 정보를 저장하는 테이블입니다. 이 테이블의 'loan'은 은행으로부터 받는 실제 대출을 의미하며, loans 테이블의 'loan'(전기 바이크 대여 계약)과는 다른 개념입니다. 이 테이블은 은행 대출의 기본 정보, 대출 조건, 상환 스케줄 등을 포함합니다.
        loan_id text NOT NULL,              -- 각 대출을 고유하게 식별하기 위해 부여되는 고유 번호와 문자열의 조합. A unique number/string for each loan.
        bank text NULL,                     -- 대출(loan)을 제공하는 은행의 이름을 저장하는 필드.
        bank_loan_code text NOT NULL,       -- 은행에서 대출 상품을 식별하기 위해 내부적으로 사용하는 코드이다.
        ev_brand text NULL,                 -- 전기 바이크 브랜드 이름을 나타내는 텍스트 필드이다.
        "#_of_evs" int8 NULL,               -- 해당 계약에 포함된 전기 바이크의 총 대수이다.
        agreement_no text NULL,             -- 대출 계약을 고유하게 식별하기 위해 부여되는 식별자이다. (예 : Agreement No 1)
        agreement_date timestamp NULL,      -- 대출 계약 체결일을 YYYY-MM-DD 형식으로 저장한다.
        disbursement_date timestamp NULL,   -- 대출금이 실제로 지급된 날짜를 YYYY-MM-DD 형식으로 저장한다.
        principal float8 NULL,              -- 예정된 원금 상환 금액을 저장하는 필드이다.
        interest int8 NULL,                 -- 예정된 이자 상환 금액을 저장하는 필드이다.
        installment float8 NULL,            -- 각 상환 회차(월)에서 납부해야하는 정기 상환 금액(원금과 이자를 합한 총액을 전체 계약 기간으로 나눈 것)을 저장하는 필드이다.
        loan_tenure float8 NULL,            -- 대출의 전체 기간을 개월(months) 단위로 저장하는 필드이다.
        total_loan_payables int8 NULL,      -- 원금과 이자를 합산하여 계산한 해당 대출의 총 납부 금액이다.
        interest_from_bank float8 NULL,     -- 은행에서 제공하는 이자율(%)을 소수 형태로 저장하는 필드이다. (예 : 6.9%는 0.069로 기록).
        CONSTRAINT master_loans_pkey PRIMARY KEY (loan_id, bank_loan_code),
        CONSTRAINT fk_master_loans_loan_id FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
    );
    """,
]