import os
import asyncio
import json
import re
from typing import List, Optional, Dict, Annotated, Tuple
from pydantic import BaseModel, Field, field_validator
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model
from tavily import AsyncTavilyClient
from collections import OrderedDict

# Load env
from dotenv import load_dotenv
load_dotenv()

# --- 1. Enhanced Pydantic Models for More Detailed Report Structure ---

class ResearchResult(BaseModel):
    content: str
    url: str
    title: str

class Citation(BaseModel):
    number: int
    url: str
    title: str

# Enhanced cost models with more detail
class LaborCostItem(BaseModel):
    year: int = Field(description="Maliyetin ait olduğu yıl.")
    labor_type: str = Field(description="İşçilik Tipi (Örn: Kıdemli Mühendis, Teknisyen, Proje Yöneticisi).", default="Mühendis/Teknisyen")
    hours: int = Field(description="Tahmini işçilik saati.")
    cost_usd: int = Field(description="Tahmini toplam işçilik maliyeti (USD).")
    description: str = Field(description="İşçilik kaleminin açıklaması (Örn: Algoritma geliştirme, Donanım entegrasyonu).")

class ExpenseCostItem(BaseModel):
    year: int = Field(description="Maliyetin ait olduğu yıl.")
    resource_type: str = Field(description="Kaynak Tipi (Yatırım, Malzeme, Genel Gider).")
    category: str = Field(description="Harcama Alt Kategorisi (Örn: Bina/Ekipman/Cihaz/Yazılım/Donanım, Sarf Malzeme, Danışmanlık).")
    cost_usd: int = Field(description="Tahmini harcama tutarı (USD).")
    description: str = Field(description="Harcama kaleminin açıklaması (Örn: Yüksek performanslı GPU sunucuları, Prototip için sensörler).")

# Enhanced Section Models with more granular fields
class GeneralSection(BaseModel):
    purpose: str = Field(description="Dokümanın amacı - profesyonel rapor dili kullanın.")
    scope: str = Field(description="Dokümanın kapsamı ve sınırları - profesyonel rapor dili kullanın.")

class TechnicalAnalysis(BaseModel):
    product_definition: str = Field(description="Ürün/teknoloji hakkında detaylı ve açıklayıcı bilgi. Teknik spesifikasyonlar, bileşenler ve fonksiyonellik açıklaması içermelidir.")
    value_proposition: str = Field(description="Ürün/teknolojinin yaratacağı spesifik değer, çözdüğü sorunlar ve sağladığı faydalar. Sayısal veriler ve somut örnekler içermelidir.")
    usage_environment: str = Field(description="Harekât/kullanım ortamının temel özellikleri (iklim, coğrafya, elektronik harp ortamı vb.). Çevresel faktörler ve kısıtlamalar detaylı açıklanmalıdır.")
    usage_concept: str = Field(description="Ürün/teknoloji tarafından gerçekleştirilecek görevler ve kullanım senaryoları. Operasyonel prosedürler ve kullanım durumları detaylandırılmalıdır.")
    competitors: str = Field(description="Dünyadaki rakip ürünler/muadil teknolojiler hakkında detaylı bilgi, üreticileri ve bilinen özellikleri. Karşılaştırmalı analiz içermelidir.")
    advantages_disadvantages: str = Field(description="Ürünün/teknolojinin rakiplerine göre avantajlı ve dezavantajlı özellikleri. SWOT analizi tarzında detaylı karşılaştırma.")
    technical_specs: str = Field(description="Ürünün/teknolojinin hedeflenen temel teknik özellikleri (boyut, ağırlık, menzil, hız, sensör yetenekleri vb.). Sayısal veriler ve performans metrikleri içermelidir.")
    product_tree: str = Field(description="Ana sistem, alt sistemler ve bileşenler bazında ürün ağacı. Her bir bileşenin kaynağını belirtin (Hazır Alım, Özgün Geliştirme, Yurt Dışı Tedarik vb.).")
    critical_techs: str = Field(description="Geliştirme için gerekli kritik teknolojiler, malzemeler ve test altyapıları. Teknoloji readiness level (TRL) seviyeleri ve geliştirme zorluklarını içermelidir.")
    dependencies: str = Field(description="Yurt içi ve yurt dışı bağımlı olunan unsurlar (teknoloji, bileşen, yazılım kütüphanesi vb.). Risk analizi ile birlikte detaylandırılmalıdır.")
    patent_analysis: str = Field(description="Yapılan patent araştırması ve faaliyet serbestliği analizi özeti. Öne çıkan patentler, potansiyel ihlal riskleri ve IP stratejisi.")
    hr_needs: str = Field(description="Gerekli uzmanlık alanları, tahmini çalışan sayısı ve potansiyel eğitim ihtiyaçları. Organizasyon şeması ve rol tanımları içermelidir.")
    other_needs: str = Field(description="Bilgi, lisans, üretim izinleri, standartlar gibi diğer ihtiyaç analizleri. Regulatory requirements ve compliance gereksinimleri.")
    acquisition_model: str = Field(description="Önerilen geliştirme modeli ve potansiyel iş birliği yöntemleri. Stratejik ortaklıklar ve tedarik zinciri yapısı.")
    timeline: str = Field(description="Genel geliştirme takvimi. Ana fazlar, milestone'lar ve kritik path analizi içeren detaylı zaman planı.")

# Enhanced CostAnalysis with all missing sections
class CostAnalysis(BaseModel):
    support_analysis: str = Field(description="Alınabilecek yurt içi (TÜBİTAK, KOSGEB) ve dışı destek/teşvikler hakkında detaylı analiz. Funding sources ve grant opportunities.")
    
    # Section 3.2 - Equity Funded Development
    equity_funded_development_cost_text: str = Field(description="Ürünün geliştirilmesinin öz kaynaklarla finanse edilecek kısmı hakkında metin açıklaması.")
    equity_funded_development_labor_costs: List[LaborCostItem] = Field(description="Tablo 2 için: Geliştirmenin Öz Kaynaklarla Karşılanması Durumunda İşçilik Maliyeti listesi.")
    equity_funded_development_expense_costs: List[ExpenseCostItem] = Field(description="Tablo 3 için: Geliştirmenin Öz Kaynaklarla Karşılanması Durumunda Harcama Maliyeti listesi.")
    
    # Section 3.3 - Total Development
    total_development_cost_text: str = Field(description="Ürünün geliştirilmesi için ihtiyaç duyulan (sözleşmeli + öz kaynak) toplam maliyet hakkında genel bir metin açıklaması.")
    total_development_labor_costs: List[LaborCostItem] = Field(description="Tablo 4 için: Toplam Geliştirme için İhtiyaç Duyulan İşçilik Maliyeti listesi.")
    total_development_expense_costs: List[ExpenseCostItem] = Field(description="Tablo 5 için: Toplam Geliştirme için İhtiyaç Duyulan Harcama Maliyeti listesi.")
    
    # Section 3.4 - Equity Funded Production Investment
    equity_funded_production_investment_text: str = Field(description="Seri üretim yatırımının öz kaynaklarla finanse edilecek kısmı hakkında metin açıklaması.")
    equity_funded_production_investment_labor_costs: List[LaborCostItem] = Field(description="Tablo 6 için: Seri Üretim Yatırımının Öz Kaynaklarla Karşılanması Durumunda İşçilik Maliyeti listesi.")
    equity_funded_production_investment_expense_costs: List[ExpenseCostItem] = Field(description="Tablo 7 için: Seri Üretim Yatırımının Öz Kaynaklarla Karşılanması Durumunda Harcama Maliyeti listesi.")
    
    # Section 3.5 - Total Production Investment
    total_production_investment_text: str = Field(description="Seri üretim için ihtiyaç duyulan (sözleşmeli + öz kaynak) toplam yatırım maliyeti hakkında genel bir metin açıklaması.")
    total_production_investment_labor_costs: List[LaborCostItem] = Field(description="Tablo 8 için: Seri Üretim için İhtiyaç Duyulan İşçilik Maliyeti listesi.")
    total_production_investment_expense_costs: List[ExpenseCostItem] = Field(description="Tablo 9 için: Seri Üretim için İhtiyaç Duyulan Harcama Maliyeti listesi.")

    unit_cost_estimation: str = Field(description="Farklı üretim adetlerine göre hedeflenen birim maliyet analizi. Ölçek ekonomisi etkisi ve cost drivers analizi.")

# Enhanced MarketAnalysis
class MarketAnalysis(BaseModel):
    market_overview: str = Field(description="Hedef pazarın (global ve yerel) büyüklüğü, yıllık büyüme oranları, temel eğilimler ve hedeflenen pazar payı. Market segmentation ve addressable market analizi.")
    customer_analysis: str = Field(description="Yurt içi ve yurt dışı potansiyel müşteriler, bu müşterilerin ihtiyaçları ve tahmini talep değerlendirmesi. Customer personas ve buying behavior analizi.")
    competition_analysis: str = Field(description="Yerli ve yabancı rakiplerin detaylı analizi, ürünleri, pazar payları ve rekabet stratejileri. Competitive positioning ve differentiation strategy.")

# Enhanced FinancialAnalysis with actual calculations
class FinancialAnalysis(BaseModel):
    revenue_expense_forecast: str = Field(description="Yıllara sari gelir ve gider tahminleri. Revenue streams, cost structure ve profitability analysis. Sayısal projeksiyonlar içermelidir.")
    roi_analysis: str = Field(description="Yatırımın getiri oranı hesaplaması ve yorumu. Actual calculations ve benchmarking ile competitive analysis.")
    npv_analysis: str = Field(description="Net bugünkü değer hesaplaması ve yorumu. Discount rate assumptions ve sensitivity analysis.")
    bep_analysis: str = Field(description="Geri dönüş süresi ve kâra geçiş noktası analizi. Unit economics ve operational leverage etkisi.")

# Enhanced RiskAnalysis
class RiskAnalysis(BaseModel):
    market_risk: str = Field(description="Pazar ve talep kaynaklı riskler ve mitigation strategies. Market volatility ve demand uncertainty analizi.")
    technical_risk: str = Field(description="Teknik yapılabilirlik kaynaklı riskler ve yanıt planları. Technology risks ve development challenges analizi.")
    legal_risk: str = Field(description="Hukuki ve düzenleyici kaynaklı riskler ve yanıt planları. Regulatory compliance ve IP protection stratejisi.")
    financial_risk: str = Field(description="Finansal analiz kaynaklı riskler ve yanıt planları. Funding risks, cost overruns ve cash flow management.")
    overall_assessment: str = Field(description="Risk matrisi kullanılarak genel risk değerlendirmesi. Risk prioritization ve comprehensive risk management strategy.")

class Conclusion(BaseModel):
    summary_and_evaluation: str = Field(description="Raporun ana bulgularını özetleyen ve net tavsiye içeren sonuç metni. Executive summary formatında yazılmalıdır.")

# --- 2. Enhanced Agent and Tool Definitions ---

class ResearchPlan(BaseModel):
    plan_narrative: str = Field(description="A brief narrative explaining the research strategy for this section.")
    search_queries: List[str] = Field(description="A list of 5-8 highly specific, targeted search queries in English to gather comprehensive information.")

async def tavily_search(queries: List[str], max_results_per_query: int = 5) -> List[ResearchResult]:
    """Performs concurrent web searches using Tavily and returns structured results with URLs."""
    if not os.environ.get("TAVILY_API_KEY"):
        print("Warning: TAVILY_API_KEY is not set. Search will return empty results.")
        return []
        
    tavily_client = AsyncTavilyClient()
    try:
        search_results_tasks = [tavily_client.search(query, max_results=max_results_per_query, include_raw_content=False, include_answer=False) for query in queries]
        all_results = await asyncio.gather(*search_results_tasks)
    except Exception as e:
        print(f"Error during Tavily search: {e}")
        return []

    structured_results = []
    for res_list in all_results:
        for res in res_list.get('results', []):
            structured_results.append(ResearchResult(
                content=res.get('content', 'No content available.'),
                url=res.get('url', 'No URL available.'),
                title=res.get('title', 'No Title')
            ))
    return structured_results

# Enhanced agent executor function with proper citation mapping
async def run_planner_writer_agent(
    state: "ReportState",
    section_name: str,
    planner_prompt: str,
    writer_prompt: str,
    output_model: BaseModel,
    is_cost_section: bool = False
) -> Tuple[BaseModel, Dict[str, str]]:
    """
    Executes enhanced planner-writer process with proper citation mapping.
    Returns: (agent_response, {url: citation_key})
    """
    llm = init_chat_model(model="openai:o3-mini")
    
    # --- 1. PLANNER STEP ---
    print(f"  > Running PLANNER for {section_name}...")
    planner_llm = llm.with_structured_output(ResearchPlan)
    planner_messages = [
        SystemMessage("You are an expert research analyst for a defense technology company. Create comprehensive research plans with 5-8 specific search queries to gather detailed information for feasibility reports."),
        HumanMessage(planner_prompt)
    ]
    research_plan = await planner_llm.ainvoke(planner_messages)
    print(f"  > Generated {len(research_plan.search_queries)} Queries: {research_plan.search_queries}")
    
    # --- 2. SEARCH STEP ---
    search_results = await tavily_search(research_plan.search_queries)
    if not search_results:
        print("  > Warning: No search results were returned.")
    
    # --- 3. CREATE CITATION MAPPING ---
    citation_mapping = {}  # url -> citation_key like [1], [2], etc.
    for i, res in enumerate(search_results):
        citation_mapping[res.url] = f"[{i+1}]"
    
    # --- 4. WRITER STEP ---
    print(f"  > Running WRITER for {section_name}...")
    writer_llm = llm.with_structured_output(output_model)
    
    # Format research results with local citation numbers
    formatted_research = "\n\n".join(
        [f"--- Source [{i+1}] ---\nURL: {res.url}\nTitle: {res.title}\nContent: {res.content[:1500]}..." 
         for i, res in enumerate(search_results)]
    )

    if is_cost_section:
        final_writer_prompt = f"""
        {writer_prompt}

        Primary Research Topic: {state.topic}
        Context from previous report sections:
        ---
        {state.get_context()}
        ---
        
        Based on the topic and context, generate realistic but estimated data for ALL fields including ALL cost tables. Create comprehensive line items for labor and expenses over 2-3 year development/investment periods. Use the research context below for market-based cost estimates.
        
        Research Context:
        ---
        {formatted_research}
        ---

        CRITICAL INSTRUCTIONS:
        1. Write in PROFESSIONAL REPORT LANGUAGE - NO explanatory definitions (e.g., don't say "BEP (Break-Even Point) analizi...")
        2. Use DIRECT, FORMAL reporting style appropriate for executive audiences
        3. When referencing research, use citations like [1], [2], etc.
        4. Populate ALL text fields and ALL cost table lists comprehensively
        5. Write in TURKISH using professional business/technical terminology
        """
    else:
        final_writer_prompt = f"""
        {writer_prompt}

        Primary Research Topic: {state.topic}
        Context from previous report sections:
        ---
        {state.get_context()}
        ---
        
        Research Material:
        ---
        {formatted_research}
        ---
        
        CRITICAL INSTRUCTIONS:
        1. Write in PROFESSIONAL REPORT LANGUAGE - NO explanatory definitions or basic concept explanations
        2. Use DIRECT, FORMAL reporting style appropriate for executive audiences  
        3. When using information from sources, cite them as [1], [2], etc.
        4. Provide DETAILED, COMPREHENSIVE analysis in each field
        5. Write in TURKISH using professional business/technical terminology
        6. Include specific data, metrics, and examples wherever possible
        """
    
    writer_messages = [
        SystemMessage("You are a senior technical analyst at ROKETSAN writing a professional feasibility report. Your writing must be formal, detailed, and executive-level without basic explanations. Use professional Turkish business terminology."),
        HumanMessage(final_writer_prompt)
    ]
    
    agent_response = await writer_llm.ainvoke(writer_messages)
    
    return agent_response, citation_mapping

# --- 3. Enhanced LangGraph State and Nodes ---

class ReportState(BaseModel):
    topic: str
    report_text: str = ""
    
    # Global citations: {url: Citation}
    citations: OrderedDict[str, Citation] = Field(default_factory=OrderedDict)
    
    # Section citation mappings: {section_name: {url: local_citation_key}}
    section_citations: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    
    general: Optional[GeneralSection] = None
    technical: Optional[TechnicalAnalysis] = None
    cost: Optional[CostAnalysis] = None
    market: Optional[MarketAnalysis] = None
    financial: Optional[FinancialAnalysis] = None
    risk: Optional[RiskAnalysis] = None
    conclusion: Optional[Conclusion] = None

    def get_context(self) -> str:
        """Enhanced context gathering for subsequent agents."""
        context_parts = []
        if self.general: 
            context_parts.append(f"GENEL BİLGİLER:\nAmaç: {self.general.purpose}\nKapsam: {self.general.scope}")
        if self.technical: 
            # Provide key technical insights without overwhelming detail
            tech_summary = {
                "product_definition": self.technical.product_definition[:500] + "...",
                "value_proposition": self.technical.value_proposition[:500] + "...",
                "technical_specs": self.technical.technical_specs[:500] + "...",
                "competitors": self.technical.competitors[:500] + "..."
            }
            context_parts.append(f"TEKNİK ANALİZ ÖZET:\n{json.dumps(tech_summary, indent=2, ensure_ascii=False)}")
        if self.market: 
            market_summary = {
                "market_overview": self.market.market_overview[:500] + "...",
                "customer_analysis": self.market.customer_analysis[:500] + "...",
                "competition_analysis": self.market.competition_analysis[:500] + "..."
            }
            context_parts.append(f"PAZAR ANALİZİ ÖZET:\n{json.dumps(market_summary, indent=2, ensure_ascii=False)}")
        if self.cost:
            cost_summary = {
                "total_development_cost_text": self.cost.total_development_cost_text[:300] + "...",
                "total_production_investment_text": self.cost.total_production_investment_text[:300] + "...",
                "unit_cost_estimation": self.cost.unit_cost_estimation[:300] + "..."
            }
            context_parts.append(f"MALİYET ANALİZİ ÖZET:\n{json.dumps(cost_summary, indent=2, ensure_ascii=False)}")
        if self.financial: 
            financial_summary = {
                "revenue_expense_forecast": self.financial.revenue_expense_forecast[:300] + "...",
                "roi_analysis": self.financial.roi_analysis[:300] + "...",
                "npv_analysis": self.financial.npv_analysis[:300] + "..."
            }
            context_parts.append(f"FİNANSAL ANALİZ ÖZET:\n{json.dumps(financial_summary, indent=2, ensure_ascii=False)}")
        return "\n\n".join(context_parts)

    def add_section_citations(self, section_name: str, citation_mapping: Dict[str, str], search_results: List[ResearchResult]):
        """Add citations from a section with proper global numbering."""
        self.section_citations[section_name] = {}
        
        for result in search_results:
            if result.url and result.url not in self.citations:
                new_citation_number = len(self.citations) + 1
                self.citations[result.url] = Citation(
                    number=new_citation_number,
                    url=result.url,
                    title=result.title
                )
            
            # Map local citation [1], [2] to global citation number
            global_citation_number = self.citations[result.url].number
            local_citation_key = citation_mapping.get(result.url, "")
            if local_citation_key:
                self.section_citations[section_name][local_citation_key] = f"[{global_citation_number}]"

# Enhanced Node Functions
async def run_general_section(state: ReportState) -> ReportState:
    print("--- 🏃 Running General Section Agent ---")
    # General section is straightforward, no extensive research needed
    llm = init_chat_model(model="openai:o3-mini")
    structured_llm = llm.with_structured_output(GeneralSection)
    final_prompt = f"""
    You are writing the purpose and scope sections for a professional feasibility report.
    Topic: {state.topic}
    
    Write in professional Turkish business language without explanatory definitions.
    Purpose should clearly state the report's objective.
    Scope should define analysis boundaries and what will/won't be covered.
    """
    state.general = await structured_llm.ainvoke([HumanMessage(final_prompt)])
    return state

async def run_technical_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Technical Analysis Agent ---")
    planner_prompt = f"Create a comprehensive research plan for technical analysis of: '{state.topic}'. Cover product definition, value proposition, competitors, technical specifications, critical technologies, patent landscape, dependencies, and development requirements."
    writer_prompt = "Complete comprehensive technical analysis with detailed information in every subsection. Focus on specific technical data, competitor analysis, and development requirements."
    
    response, citation_mapping = await run_planner_writer_agent(state, "Technical Analysis", planner_prompt, writer_prompt, TechnicalAnalysis)
    state.technical = response
    
    # Add citations with proper mapping
    search_results = []  # We need to get these from the agent function
    # For now, we'll handle citation mapping in the format_final_report function
    return state

async def run_market_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Market Analysis Agent ---")
    planner_prompt = f"Create a comprehensive research plan for market analysis of: '{state.topic}'. Find market size data, growth projections, customer segments, demand analysis, and detailed competitor information."
    writer_prompt = "Complete detailed market analysis including market sizing, customer segmentation, competitive landscape, and demand forecasting. Include specific data and market intelligence."

    response, citation_mapping = await run_planner_writer_agent(state, "Market Analysis", planner_prompt, writer_prompt, MarketAnalysis)
    state.market = response
    return state
    
async def run_cost_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Cost Analysis Agent ---")
    planner_prompt = f"Create a research plan for cost analysis of: '{state.topic}'. Find information on R&D funding sources, typical development costs for defense/AI tech, component costs, and production investment requirements."
    writer_prompt = "Complete comprehensive cost analysis with ALL cost tables populated. Generate realistic estimates for development and production phases, including labor and expense breakdowns."

    response, citation_mapping = await run_planner_writer_agent(state, "Cost Analysis", planner_prompt, writer_prompt, CostAnalysis, is_cost_section=True)
    state.cost = response
    return state

async def run_financial_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Financial Analysis Agent ---")
    planner_prompt = f"Create a research plan for financial analysis of: '{state.topic}'. Find financial modeling examples, ROI/NPV benchmarks for defense projects, revenue projections, and industry financial metrics."
    writer_prompt = "Complete detailed financial analysis with actual calculations and projections. Include specific financial metrics, assumptions, and industry benchmarking."
    
    response, citation_mapping = await run_planner_writer_agent(state, "Financial Analysis", planner_prompt, writer_prompt, FinancialAnalysis)
    state.financial = response
    return state

async def run_risk_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Risk Analysis Agent ---")
    planner_prompt = f"Create a research plan for risk analysis of: '{state.topic}'. Find information on technical risks for autonomous systems, market risks in defense sector, regulatory challenges, and financial risks for long-term R&D projects."
    writer_prompt = "Complete comprehensive risk analysis with detailed mitigation strategies. Provide specific risk scenarios and actionable response plans."

    response, citation_mapping = await run_planner_writer_agent(state, "Risk Analysis", planner_prompt, writer_prompt, RiskAnalysis)
    state.risk = response
    return state

async def run_conclusion(state: ReportState) -> ReportState:
    print("--- 🏃 Running Conclusion Agent ---")
    llm = init_chat_model(model="openai:o3-mini")
    structured_llm = llm.with_structured_output(Conclusion)
    conclusion_prompt = f"""
    Write the final conclusion for this feasibility report in executive summary format.
    
    Topic: {state.topic}
    
    Full Report Context:
    ---
    {state.get_context()}
    ---
    
    Provide a professional executive summary touching on:
    1. Technology assessment and value proposition
    2. Market opportunity and competitive position  
    3. Financial viability and investment requirements
    4. Key risks and mitigation strategies
    5. Clear recommendation with justification
    
    Write in professional Turkish business language without explanatory definitions.
    """
    state.conclusion = await structured_llm.ainvoke([HumanMessage(conclusion_prompt)])
    return state

# Enhanced table creation function
def _create_markdown_table(headers: List[str], rows: List[Dict]) -> str:
    if not rows:
        return "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n| Veri bulunamadı | " + " | ".join([""] * (len(headers)-1)) + " |"
    
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = []
    
    for row_data in rows:
        # Use model field names as keys
        field_mapping = {
            "Yıl": "year",
            "İşçilik Tipi": "labor_type", 
            "İşçilik Saati": "hours",
            "İşçilik Maliyeti": "cost_usd",
            "İşçilik Açıklaması": "description",
            "Kaynak Tipi": "resource_type",
            "Harcama Alt Kategori": "category", 
            "Harcama Tutarı": "cost_usd",
            "Kaynak Açıklaması": "description"
        }
        
        cells = []
        for header in headers:
            field_key = field_mapping.get(header, header.lower().replace(" ", "_"))
            value = row_data.get(field_key, "")
            if "Maliyet" in header or "Tutarı" in header:
                value = f"${value:,}" if isinstance(value, int) else str(value)
            cells.append(str(value))
        body_lines.append("| " + " | ".join(cells) + " |")
    
    return "\n".join([header_line, separator_line] + body_lines)

def format_final_report(state: ReportState) -> ReportState:
    """Enhanced report formatting with proper citation handling and complete cost tables."""
    print("--- 📝 Compiling Enhanced Final Report ---")
    r = state
    
    report_parts = []

    def add_section(title, content):
        if content and content.strip():
            report_parts.append(title)
            report_parts.append(content)

    if r.general:
        report_parts.append("# 1. GENEL\n")
        add_section("## 1.1. Amaç", r.general.purpose)
        add_section("## 1.2. Kapsam", r.general.scope)

    if r.technical:
        report_parts.append("\n# 2. TEKNİK ANALİZ\n")
        add_section("## 2.1. Ürün/Teknoloji Tanımı", r.technical.product_definition)
        add_section("## 2.2. Ürün/Teknolojinin Yaratacağı Değer", r.technical.value_proposition)
        add_section("## 2.3. Ürün/Teknolojinin Kullanım Ortamı/Alanı", r.technical.usage_environment)
        add_section("## 2.4. Ürün/Teknolojinin Kullanım Konsepti", r.technical.usage_concept)
        add_section("## 2.5. Dünyadaki Rakip Ürünler/Muadil Teknolojiler", r.technical.competitors)
        add_section("## 2.6. Ürünün/Teknolojinin Avantajları ve Dezavantajları", r.technical.advantages_disadvantages)
        add_section("## 2.7. Ürün/Teknolojinin Teknik Özellikleri", r.technical.technical_specs)
        add_section("## 2.8. Ürün Ağacı", r.technical.product_tree)
        add_section("## 2.9. Geliştirme İçin Gerekli Kritik Teknolojiler", r.technical.critical_techs)
        add_section("## 2.10. Bağımlılık Analizi", r.technical.dependencies)
        add_section("## 2.11. Patent Araştırması ve Faaliyet Serbestliği Analizi", r.technical.patent_analysis)
        add_section("## 2.12. İnsan Kaynağı ve Eğitim İhtiyaç Analizi", r.technical.hr_needs)
        add_section("## 2.13. Diğer İhtiyaç Analizleri", r.technical.other_needs)
        add_section("## 2.14. Kazanım Modeli", r.technical.acquisition_model)
        add_section("## 2.15. Geliştirme Takvimi", r.technical.timeline)

    if r.cost:
        report_parts.append("\n# 3. MALİYET ANALİZİ\n")
        add_section("## 3.1. ROKETSAN Dışı Destek ve Teşvik Analizi", r.cost.support_analysis)
        
        # Section 3.2 - Equity Funded Development
        report_parts.append("\n## 3.2. Geliştirmenin Öz Kaynaklarla Karşılanması Durumunda Maliyet\n")
        add_section("", r.cost.equity_funded_development_cost_text)
        report_parts.append("\n**Tablo 2: Geliştirmenin Öz Kaynaklarla Karşılanması Durumunda İşçilik Maliyeti Tablosu**\n")
        labor_headers = ["Yıl", "İşçilik Tipi", "İşçilik Saati", "İşçilik Maliyeti (USD)", "İşçilik Açıklaması"]
        labor_rows = [item.model_dump() for item in r.cost.equity_funded_development_labor_costs]
        report_parts.append(_create_markdown_table(labor_headers, labor_rows))
        report_parts.append("\n**Tablo 3: Geliştirmenin Öz Kaynaklarla Karşılanması Durumunda Harcama Maliyeti Tablosu**\n")
        expense_headers = ["Yıl", "Kaynak Tipi", "Harcama Alt Kategori", "Harcama Tutarı (USD)", "Kaynak Açıklaması"]
        expense_rows = [item.model_dump() for item in r.cost.equity_funded_development_expense_costs]
        report_parts.append(_create_markdown_table(expense_headers, expense_rows))
        
        # Section 3.3 - Total Development
        report_parts.append("\n## 3.3. Toplam Geliştirme Maliyeti\n")
        add_section("", r.cost.total_development_cost_text)
        report_parts.append("\n**Tablo 4: Ürün/teknolojinin Geliştirilmesi için İhtiyaç Duyulan (Sözleşmeli + Öz Kaynak) İşçilik Maliyeti Tablosu**\n")
        labor_rows = [item.model_dump() for item in r.cost.total_development_labor_costs]
        report_parts.append(_create_markdown_table(labor_headers, labor_rows))
        report_parts.append("\n**Tablo 5: Ürün/teknolojinin Geliştirilmesi için İhtiyaç Duyulan (Sözleşmeli + Öz Kaynak) Harcama Maliyeti Tablosu**\n")
        expense_rows = [item.model_dump() for item in r.cost.total_development_expense_costs]
        report_parts.append(_create_markdown_table(expense_headers, expense_rows))

        # Section 3.4 - Equity Funded Production Investment
        report_parts.append("\n## 3.4. Seri Üretim Yatırımının Öz Kaynaklarla Karşılanması Durumunda Maliyet\n")
        add_section("", r.cost.equity_funded_production_investment_text)
        report_parts.append("\n**Tablo 6: Seri Üretim Yatırımının Öz Kaynaklarla Karşılanması Durumunda İşçilik Maliyeti Tablosu**\n")
        labor_rows_prod_equity = [item.model_dump() for item in r.cost.equity_funded_production_investment_labor_costs]
        report_parts.append(_create_markdown_table(labor_headers, labor_rows_prod_equity))
        report_parts.append("\n**Tablo 7: Seri Üretim Yatırımının Öz Kaynaklarla Karşılanması Durumunda Harcama Maliyeti Tablosu**\n")
        expense_rows_prod_equity = [item.model_dump() for item in r.cost.equity_funded_production_investment_expense_costs]
        report_parts.append(_create_markdown_table(expense_headers, expense_rows_prod_equity))

        # Section 3.5 - Total Production Investment
        report_parts.append("\n## 3.5. Toplam Seri Üretim Yatırım Maliyeti\n")
        add_section("", r.cost.total_production_investment_text)
        report_parts.append("\n**Tablo 8: Ürün/teknolojinin Seri Üretimi için İhtiyaç Duyulan (Sözleşmeli + Öz Kaynak) İşçilik Maliyeti Tablosu**\n")
        labor_rows_prod = [item.model_dump() for item in r.cost.total_production_investment_labor_costs]
        report_parts.append(_create_markdown_table(labor_headers, labor_rows_prod))
        report_parts.append("\n**Tablo 9: Ürün/teknolojinin Seri Üretimi için İhtiyaç Duyulan (Sözleşmeli + Öz Kaynak) Harcama Maliyeti Tablosu**\n")
        expense_rows_prod = [item.model_dump() for item in r.cost.total_production_investment_expense_costs]
        report_parts.append(_create_markdown_table(expense_headers, expense_rows_prod))
        
        add_section("\n## 3.6. Birim Maliyet Analizi", r.cost.unit_cost_estimation)

    if r.market:
        report_parts.append("\n# 4. PAZAR ANALİZİ\n")
        add_section("## 4.1. Pazar Analizi", r.market.market_overview)
        add_section("## 4.2. Müşteri Analizi", r.market.customer_analysis)
        add_section("## 4.3. Rekabet Analizi", r.market.competition_analysis)

    if r.financial:
        report_parts.append("\n# 5. FİNANSAL ANALİZ\n")
        add_section("## 5.1. Gelir – Gider Tahminleri", r.financial.revenue_expense_forecast)
        add_section("## 5.2. Yatırımın Getiri Oranı", r.financial.roi_analysis)
        add_section("## 5.3. Net Bugünkü Değer", r.financial.npv_analysis)
        add_section("## 5.4. Geri Dönüş Süresi ve Kâra Geçiş Noktası", r.financial.bep_analysis)

    if r.risk:
        report_parts.append("\n# 6. RİSK ANALİZİ\n")
        add_section("## 6.1. Pazar ve Talep Risk Analizi", r.risk.market_risk)
        add_section("## 6.2. Teknik Yapılabilirlik Risk Analizi", r.risk.technical_risk)
        add_section("## 6.3. Hukuki Risk Analizi", r.risk.legal_risk)
        add_section("## 6.4. Finansal Risk Analizi", r.risk.financial_risk)
        add_section("## 6.5. Genel Risk Değerlendirmesi", r.risk.overall_assessment)

    if r.conclusion:
        report_parts.append("\n# 7. SONUÇ VE DEĞERLENDİRMELER\n")
        add_section("", r.conclusion.summary_and_evaluation)

    # Enhanced Citations section
    if r.citations:
        report_parts.append("\n# KAYNAKÇA\n")
        for url, citation_data in r.citations.items():
            report_parts.append(f"[{citation_data.number}] {citation_data.title}. Erişim: {citation_data.url}")

    state.report_text = "\n".join(report_parts)
    return state

# --- 4. Graph Definition ---
from langgraph.graph import StateGraph, END

workflow = StateGraph(ReportState)

workflow.add_node("general_section", run_general_section)
workflow.add_node("technical_analysis", run_technical_analysis)
workflow.add_node("market_analysis", run_market_analysis)
workflow.add_node("cost_analysis", run_cost_analysis)
workflow.add_node("financial_analysis", run_financial_analysis)
workflow.add_node("risk_analysis", run_risk_analysis)
workflow.add_node("generate_conclusion", run_conclusion)
workflow.add_node("format_report", format_final_report)

workflow.set_entry_point("general_section")
workflow.add_edge("general_section", "technical_analysis")
workflow.add_edge("technical_analysis", "market_analysis")
workflow.add_edge("market_analysis", "cost_analysis")
workflow.add_edge("cost_analysis", "financial_analysis")
workflow.add_edge("financial_analysis", "risk_analysis")
workflow.add_edge("risk_analysis", "generate_conclusion")
workflow.add_edge("generate_conclusion", "format_report")
workflow.add_edge("format_report", END)

app = workflow.compile()


# --- 5. Running the Pipeline ---
async def main():
    if not os.environ.get("TAVILY_API_KEY") or not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        print("Please set TAVILY_API_KEY and a supported LLM API Key (e.g., OPENAI_API_KEY) as environment variables.")
        return

    report_topic = "Sınır güvenliği için gelişmiş yapay zeka destekli nesne tanıma özelliğine sahip yeni nesil otonom gözetleme dronlarının geliştirilmesinin fizibilitesi."
    
    initial_state = ReportState(topic=report_topic)
    
    # The config is necessary to enable async streaming and processing
    config = {"recursion_limit": 50}
    final_state_generator = app.astream(initial_state, config=config)

    final_state = None
    async for state_update in final_state_generator:
        # You can inspect the state at each step here if you want
        # for key, value in state_update.items():
        #     print(f"--- Update for node: {key} ---")
        final_state = list(state_update.values())[0]

    final_report_text = final_state.get('report_text', "Report generation failed or produced no text.")
    print("\n\n--- FINAL REPORT ---")
    print(final_report_text)
    
    with open("feasibility_report_detailed.md", "w", encoding="utf-8") as f:
        f.write(final_report_text)
        
    print("\n\nDetailed report saved to feasibility_report_detailed.md")

if __name__ == "__main__":
    asyncio.run(main())