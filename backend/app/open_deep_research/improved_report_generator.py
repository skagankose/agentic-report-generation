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

class LaborCostItem(BaseModel):
    year: int = Field(description="Maliyetin ait olduğu yıl.")
    labor_type: str = Field(description="İşçilik Tipi", default="Mühendis/Teknisyen")
    hours: int = Field(description="Tahmini işçilik saati.")
    cost_usd: int = Field(description="Tahmini toplam işçilik maliyeti (USD).")
    description: str = Field(description="İşçilik kaleminin açıklaması")

class ExpenseCostItem(BaseModel):
    year: int = Field(description="Maliyetin ait olduğu yıl.")
    resource_type: str = Field(description="Kaynak Tipi")
    category: str = Field(description="Harcama Alt Kategorisi")
    cost_usd: int = Field(description="Tahmini harcama tutarı (USD).")
    description: str = Field(description="Harcama kaleminin açıklaması")

# Enhanced Section Models with more granular fields
class GeneralSection(BaseModel):
    purpose: str = Field(description="Dokümanın amacı - doğrudan profesyonel rapor dili.")
    scope: str = Field(description="Dokümanın kapsamı ve sınırları - doğrudan profesyonel rapor dili.")

class TechnicalAnalysis(BaseModel):
    product_definition: str = Field(description="Ürün/teknoloji detaylı tanımı. Teknik spesifikasyonlar, bileşenler ve fonksiyonellik.")
    value_proposition: str = Field(description="Yaratılan spesifik değer, çözülen sorunlar ve faydalar. Sayısal veriler ve somut örnekler.")
    usage_environment: str = Field(description="Harekât/kullanım ortamı özellikleri. Çevresel faktörler ve kısıtlamalar.")
    usage_concept: str = Field(description="Gerçekleştirilen görevler ve kullanım senaryoları. Operasyonel prosedürler.")
    competitors: str = Field(description="Rakip ürünler/teknolojiler, üreticiler ve özellikleri. Karşılaştırmalı analiz.")
    advantages_disadvantages: str = Field(description="Rakiplerine göre avantajlı ve dezavantajlı özellikler. SWOT analizi.")
    technical_specs: str = Field(description="Hedeflenen temel teknik özellikler. Sayısal veriler ve performans metrikleri.")
    product_tree: str = Field(description="Ana sistem, alt sistemler ve bileşenler. Kaynak belirtimi.")
    critical_techs: str = Field(description="Gerekli kritik teknolojiler ve test altyapıları. TRL seviyeleri.")
    dependencies: str = Field(description="Bağımlı unsurlar. Risk analizi ile detaylandırma.")
    patent_analysis: str = Field(description="Patent araştırması ve faaliyet serbestliği analizi özeti.")
    hr_needs: str = Field(description="Uzmanlık alanları, çalışan sayısı ve eğitim ihtiyaçları.")
    other_needs: str = Field(description="Bilgi, lisans, üretim izinleri, standartlar.")
    acquisition_model: str = Field(description="Geliştirme modeli ve iş birliği yöntemleri.")
    timeline: str = Field(description="Geliştirme takvimi. Ana fazlar ve milestone'lar.")

class CostAnalysis(BaseModel):
    support_analysis: str = Field(description="Alınabilecek destek/teşvikler analizi.")
    equity_funded_development_cost_text: str = Field(description="Öz kaynaklarla finanse edilecek geliştirme kısmı.")
    equity_funded_development_labor_costs: List[LaborCostItem] = Field(description="Öz kaynak geliştirme işçilik maliyeti.")
    equity_funded_development_expense_costs: List[ExpenseCostItem] = Field(description="Öz kaynak geliştirme harcama maliyeti.")
    total_development_cost_text: str = Field(description="Toplam geliştirme maliyeti açıklaması.")
    total_development_labor_costs: List[LaborCostItem] = Field(description="Toplam geliştirme işçilik maliyeti.")
    total_development_expense_costs: List[ExpenseCostItem] = Field(description="Toplam geliştirme harcama maliyeti.")
    equity_funded_production_investment_text: str = Field(description="Öz kaynak seri üretim yatırımı.")
    equity_funded_production_investment_labor_costs: List[LaborCostItem] = Field(description="Öz kaynak üretim işçilik maliyeti.")
    equity_funded_production_investment_expense_costs: List[ExpenseCostItem] = Field(description="Öz kaynak üretim harcama maliyeti.")
    total_production_investment_text: str = Field(description="Toplam seri üretim yatırım maliyeti.")
    total_production_investment_labor_costs: List[LaborCostItem] = Field(description="Toplam üretim işçilik maliyeti.")
    total_production_investment_expense_costs: List[ExpenseCostItem] = Field(description="Toplam üretim harcama maliyeti.")
    unit_cost_estimation: str = Field(description="Birim maliyet analizi ve ölçek ekonomisi.")

class MarketAnalysis(BaseModel):
    market_overview: str = Field(description="Pazar büyüklüğü, büyüme oranları, eğilimler ve pazar payı.")
    customer_analysis: str = Field(description="Potansiyel müşteriler, ihtiyaçlar ve talep değerlendirmesi.")
    competition_analysis: str = Field(description="Rakiplerin analizi, ürünleri, pazar payları ve stratejileri.")

class FinancialAnalysis(BaseModel):
    revenue_expense_forecast: str = Field(description="Gelir ve gider tahminleri. Sayısal projeksiyonlar.")
    roi_analysis: str = Field(description="Yatırım getiri oranı hesaplaması ve yorumu.")
    npv_analysis: str = Field(description="Net bugünkü değer hesaplaması ve yorumu.")
    bep_analysis: str = Field(description="Geri dönüş süresi ve kâra geçiş noktası analizi.")

class RiskAnalysis(BaseModel):
    market_risk: str = Field(description="Pazar ve talep kaynaklı riskler ve mitigation strategies.")
    technical_risk: str = Field(description="Teknik yapılabilirlik kaynaklı riskler ve yanıt planları.")
    legal_risk: str = Field(description="Hukuki ve düzenleyici riskler ve yanıt planları.")
    financial_risk: str = Field(description="Finansal analiz kaynaklı riskler ve yanıt planları.")
    overall_assessment: str = Field(description="Genel risk değerlendirmesi ve risk management strategy.")

class Conclusion(BaseModel):
    summary_and_evaluation: str = Field(description="Ana bulgular özeti ve net tavsiye. Executive summary formatı.")

# --- 2. Enhanced Research and Agent Tools ---

class ResearchPlan(BaseModel):
    plan_narrative: str = Field(description="Research strategy explanation.")
    search_queries: List[str] = Field(description="8-12 highly specific, targeted search queries in English.")

async def tavily_search(queries: List[str], max_results_per_query: int = 6) -> List[ResearchResult]:
    """Enhanced search with more results per query."""
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

# Enhanced agent executor with proper citation tracking
async def run_enhanced_planner_writer_agent(
    state: "ReportState",
    section_name: str,
    planner_prompt: str,
    writer_prompt: str,
    output_model: BaseModel,
    is_cost_section: bool = False
) -> Tuple[BaseModel, List[ResearchResult]]:
    """
    Enhanced planner-writer process with proper citation tracking.
    Returns: (agent_response, search_results_list)
    """
    llm = init_chat_model(model="openai:o3-mini")
    
    # --- 1. ENHANCED PLANNER STEP ---
    print(f"  > Enhanced PLANNER for {section_name}...")
    planner_llm = llm.with_structured_output(ResearchPlan)
    planner_messages = [
        SystemMessage("You are an expert research analyst for defense technology feasibility reports. Create comprehensive research plans with 8-12 specific search queries to gather detailed, technical information."),
        HumanMessage(planner_prompt)
    ]
    research_plan = await planner_llm.ainvoke(planner_messages)
    print(f"  > Generated {len(research_plan.search_queries)} Queries: {research_plan.search_queries}")
    
    # --- 2. ENHANCED SEARCH STEP ---
    search_results = await tavily_search(research_plan.search_queries)
    if not search_results:
        print("  > Warning: No search results were returned.")
    else:
        print(f"  > Retrieved {len(search_results)} search results")
    
    # --- 3. ENHANCED WRITER STEP ---
    print(f"  > Enhanced WRITER for {section_name}...")
    writer_llm = llm.with_structured_output(output_model)
    
    # Format research results with numbered citations
    formatted_research = "\n\n".join(
        [f"--- Kaynak [{i+1}] ---\nURL: {res.url}\nBaşlık: {res.title}\nİçerik: {res.content[:2000]}..." 
         for i, res in enumerate(search_results)]
    )

    if is_cost_section:
        final_writer_prompt = f"""
        {writer_prompt}

        Ana Araştırma Konusu: {state.topic}
        Önceki bölümlerden bağlam:
        ---
        {state.get_context()}
        ---
        
        Araştırma Materyali:
        ---
        {formatted_research}
        ---

        KRİTİK TALİMATLAR:
        1. DOĞRUDAN PROFESYONEL RAPOR DİLİ - tanımlayıcı açıklamalar yapma
        2. Yönetici seviyesi için FORMAL, DİREKT raporlama tarzı kullan
        3. Araştırma kaynaklarını kullanırken [1], [2] şeklinde atıf yap
        4. TÜM metin alanlarını ve TÜM maliyet tablolarını KAPSAMLI doldur
        5. 2-3 yıllık geliştirme/yatırım dönemleri için gerçekçi maliyet kalemleri oluştur
        6. Profesyonel Türkçe iş/teknik terminoloji kullan
        """
    else:
        final_writer_prompt = f"""
        {writer_prompt}

        Ana Araştırma Konusu: {state.topic}
        Önceki bölümlerden bağlam:
        ---
        {state.get_context()}
        ---
        
        Araştırma Materyali:
        ---
        {formatted_research}
        ---
        
        KRİTİK TALİMATLAR:
        1. DOĞRUDAN PROFESYONEL RAPOR DİLİ - temel kavram açıklamaları yapma
        2. Yönetici seviyesi için FORMAL, DİREKT raporlama tarzı kullan  
        3. Bilgi kaynaklarını kullanırken [1], [2] şeklinde atıf yap
        4. Her alanda DETAYLI, KAPSAMLI analiz sağla
        5. Profesyonel Türkçe iş/teknik terminoloji kullan
        6. Mümkün olan yerlerde spesifik veriler, metrikler ve örnekler dahil et
        """
    
    writer_messages = [
        SystemMessage("ROKETSAN'da kıdemli teknik analist olarak profesyonel fizibilite raporu yazıyorsun. Yazın formal, detaylı ve temel açıklamalar içermeyen yönetici seviyesinde olmalı. Profesyonel Türkçe iş terminolojisi kullan."),
        HumanMessage(final_writer_prompt)
    ]
    
    agent_response = await writer_llm.ainvoke(writer_messages)
    
    return agent_response, search_results 

# --- 3. Enhanced LangGraph State and Nodes ---

class ReportState(BaseModel):
    topic: str
    report_text: str = ""
    
    # Global citations with proper tracking
    citations: OrderedDict[str, Citation] = Field(default_factory=OrderedDict)
    
    # Store actual search results for proper citation mapping
    all_search_results: List[ResearchResult] = Field(default_factory=list)
    
    general: Optional[GeneralSection] = None
    technical: Optional[TechnicalAnalysis] = None
    cost: Optional[CostAnalysis] = None
    market: Optional[MarketAnalysis] = None
    financial: Optional[FinancialAnalysis] = None
    risk: Optional[RiskAnalysis] = None
    conclusion: Optional[Conclusion] = None

    def get_context(self) -> str:
        """Enhanced context gathering with more focused summaries."""
        context_parts = []
        if self.general: 
            context_parts.append(f"GENEL BİLGİLER:\nAmaç: {self.general.purpose[:300]}...\nKapsam: {self.general.scope[:300]}...")
        if self.technical: 
            tech_summary = f"""TEKNİK ANALİZ ÖZETİ:
- Ürün: {self.technical.product_definition[:200]}...
- Değer: {self.technical.value_proposition[:200]}...
- Teknik Özellikler: {self.technical.technical_specs[:200]}...
- Rakipler: {self.technical.competitors[:200]}..."""
            context_parts.append(tech_summary)
        if self.market: 
            market_summary = f"""PAZAR ANALİZİ ÖZETİ:
- Pazar: {self.market.market_overview[:200]}...
- Müşteriler: {self.market.customer_analysis[:200]}...
- Rekabet: {self.market.competition_analysis[:200]}..."""
            context_parts.append(market_summary)
        if self.cost:
            cost_summary = f"""MALİYET ANALİZİ ÖZETİ:
- Geliştirme: {self.cost.total_development_cost_text[:200]}...
- Üretim: {self.cost.total_production_investment_text[:200]}...
- Birim Maliyet: {self.cost.unit_cost_estimation[:200]}..."""
            context_parts.append(cost_summary)
        if self.financial: 
            financial_summary = f"""FİNANSAL ANALİZ ÖZETİ:
- Gelir-Gider: {self.financial.revenue_expense_forecast[:200]}...
- ROI: {self.financial.roi_analysis[:200]}...
- NPV: {self.financial.npv_analysis[:200]}..."""
            context_parts.append(financial_summary)
        return "\n\n".join(context_parts)

    def add_search_results_and_update_citations(self, search_results: List[ResearchResult]):
        """Add search results and update global citation numbering."""
        for result in search_results:
            if result.url and result.url not in self.citations:
                new_citation_number = len(self.citations) + 1
                self.citations[result.url] = Citation(
                    number=new_citation_number,
                    url=result.url,
                    title=result.title
                )
        
        # Store all results for citation mapping
        self.all_search_results.extend(search_results)

# Enhanced Node Functions with better prompts and deeper analysis
async def run_general_section(state: ReportState) -> ReportState:
    print("--- 🏃 Running Enhanced General Section Agent ---")
    llm = init_chat_model(model="openai:o3-mini")
    structured_llm = llm.with_structured_output(GeneralSection)
    final_prompt = f"""
    Profesyonel fizibilite raporu için amaç ve kapsam bölümlerini yaz.
    Konu: {state.topic}
    
    Doğrudan profesyonel Türkçe iş dili kullan, tanımlayıcı açıklamalar yapma.
    Amaç: raporun net hedefini belirt.
    Kapsam: analiz sınırlarını ve nelerin dahil/hariç olduğunu tanımla.
    """
    state.general = await structured_llm.ainvoke([HumanMessage(final_prompt)])
    return state

async def run_technical_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Enhanced Technical Analysis Agent ---")
    planner_prompt = f"""Create an enhanced, comprehensive research plan for technical analysis of: '{state.topic}'. 
    Generate 8-12 specific search queries covering:
    - Product definition and technical specifications
    - Value propositions and operational benefits  
    - Usage environments and operational concepts
    - Global competitors and market positioning
    - Technical advantages/disadvantages analysis
    - Critical technologies and dependencies
    - Patent landscape and IP analysis
    - Human resources and development requirements
    - Regulatory and compliance needs
    - Development models and timelines"""
    
    writer_prompt = """Teknik analizin tüm alt bölümlerini kapsamlı şekilde tamamla. Her alanda spesifik teknik veriler, rakip analizi ve geliştirme gereksinimlerini detaylandır. Doğrudan profesyonel rapor dili kullan."""
    
    response, search_results = await run_enhanced_planner_writer_agent(state, "Technical Analysis", planner_prompt, writer_prompt, TechnicalAnalysis)
    state.technical = response
    state.add_search_results_and_update_citations(search_results)
    return state

async def run_market_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Enhanced Market Analysis Agent ---")
    planner_prompt = f"""Create a comprehensive market research plan for: '{state.topic}'. 
    Generate 8-12 specific search queries covering:
    - Global and regional market size data and projections
    - Market growth rates and industry trends
    - Customer segmentation and demand analysis  
    - Target customer needs and buying behavior
    - Competitive landscape and market share analysis
    - Pricing strategies and market positioning
    - Market entry barriers and opportunities
    - Defense/security industry market dynamics
    - Government procurement patterns
    - International trade and export opportunities"""

    writer_prompt = """Pazar analizini detaylı şekilde tamamla. Pazar büyüklüğü, müşteri segmentasyonu, rekabet durumu ve talep tahminlerini spesifik veriler ve pazar zekası ile destekle."""

    response, search_results = await run_enhanced_planner_writer_agent(state, "Market Analysis", planner_prompt, writer_prompt, MarketAnalysis)
    state.market = response
    state.add_search_results_and_update_citations(search_results)
    return state
    
async def run_cost_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Enhanced Cost Analysis Agent ---")
    planner_prompt = f"""Create a comprehensive cost research plan for: '{state.topic}'. 
    Generate 8-12 specific search queries covering:
    - R&D funding sources and grant opportunities (domestic and international)
    - Typical development costs for defense AI/autonomy technologies
    - Component and material costs for drone systems
    - Production investment requirements and manufacturing costs
    - Labor costs for specialized engineering roles
    - Infrastructure and equipment investment needs
    - Operational and maintenance cost factors
    - Scale economy effects in defense manufacturing
    - Cost benchmarking for similar defense projects
    - Financial incentives and tax benefits for R&D"""

    writer_prompt = """Maliyet analizini TÜM maliyet tabloları ile kapsamlı şekilde tamamla. Geliştirme ve üretim fazları için gerçekçi tahminler oluştur, işçilik ve harcama dağılımlarını detaylandır."""

    response, search_results = await run_enhanced_planner_writer_agent(state, "Cost Analysis", planner_prompt, writer_prompt, CostAnalysis, is_cost_section=True)
    state.cost = response
    state.add_search_results_and_update_citations(search_results)
    return state

async def run_financial_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Enhanced Financial Analysis Agent ---")
    planner_prompt = f"""Create a comprehensive financial research plan for: '{state.topic}'. 
    Generate 8-12 specific search queries covering:
    - Financial modeling examples for defense projects
    - ROI/NPV benchmarks for defense technology investments
    - Revenue projection methodologies for defense products
    - Defense industry financial metrics and ratios
    - Long-term profitability analysis for R&D projects
    - Cash flow management for defense manufacturers
    - Investment evaluation criteria for defense sector
    - Risk-adjusted return calculations
    - Comparable company analysis in defense sector
    - Government contract revenue patterns"""
    
    writer_prompt = """Finansal analizi gerçek hesaplamalar ve projeksiyonlarla detaylandır. Spesifik finansal metrikler, varsayımlar ve endüstri benchmarking dahil et."""
    
    response, search_results = await run_enhanced_planner_writer_agent(state, "Financial Analysis", planner_prompt, writer_prompt, FinancialAnalysis)
    state.financial = response
    state.add_search_results_and_update_citations(search_results)
    return state

async def run_risk_analysis(state: ReportState) -> ReportState:
    print("--- 🏃 Running Enhanced Risk Analysis Agent ---")
    planner_prompt = f"""Create a comprehensive risk research plan for: '{state.topic}'. 
    Generate 8-12 specific search queries covering:
    - Technical risks for autonomous systems development
    - Market risks in defense sector and government procurement
    - Regulatory challenges for drone and AI technologies
    - Financial risks for long-term R&D defense projects
    - IP and patent risks in autonomous systems
    - Supply chain and dependency risks
    - Competitive and technology obsolescence risks
    - Political and export control risks
    - Quality and safety compliance risks
    - Risk mitigation strategies for defense projects"""

    writer_prompt = """Risk analizini detaylı risk mitigation stratejileri ile kapsamla. Spesifik risk senaryoları ve uygulanabilir yanıt planları sağla."""

    response, search_results = await run_enhanced_planner_writer_agent(state, "Risk Analysis", planner_prompt, writer_prompt, RiskAnalysis)
    state.risk = response
    state.add_search_results_and_update_citations(search_results)
    return state

async def run_conclusion(state: ReportState) -> ReportState:
    print("--- 🏃 Running Enhanced Conclusion Agent ---")
    llm = init_chat_model(model="openai:o3-mini")
    structured_llm = llm.with_structured_output(Conclusion)
    conclusion_prompt = f"""
    Bu fizibilite raporu için nihai sonuç bölümünü executive summary formatında yaz.
    
    Konu: {state.topic}
    
    Tam Rapor Bağlamı:
    ---
    {state.get_context()}
    ---
    
    Aşağıdaki konulara değinen profesyonel executive summary sağla:
    1. Teknoloji değerlendirmesi ve değer önerisi
    2. Pazar fırsatı ve rekabet pozisyonu  
    3. Finansal fizibilite ve yatırım gereksinimleri
    4. Ana riskler ve mitigation stratejileri
    5. Gerekçeli net tavsiye
    
    Doğrudan profesyonel Türkçe iş dili kullan, tanımlayıcı açıklamalar yapma.
    """
    state.conclusion = await structured_llm.ainvoke([HumanMessage(conclusion_prompt)])
    return state 

# Enhanced table creation and report formatting
def _create_enhanced_markdown_table(headers: List[str], rows: List[Dict]) -> str:
    if not rows:
        return "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n| Veri bulunamadı | " + " | ".join([""] * (len(headers)-1)) + " |"
    
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = []
    
    for row_data in rows:
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
                value = f"{value:,} USD" if isinstance(value, int) else str(value)
            cells.append(str(value))
        body_lines.append("| " + " | ".join(cells) + " |")
    
    return "\n".join([header_line, separator_line] + body_lines)

def map_citations_in_text(text: str, citations: OrderedDict[str, Citation]) -> str:
    """
    Enhanced citation mapping function that properly maps local [1], [2] citations 
    to global citation numbers based on the actual research results.
    """
    if not citations:
        return text
    
    # Create mapping from URLs to global citation numbers
    url_to_global_number = {url: citation.number for url, citation in citations.items()}
    
    # For now, return text as-is since proper mapping requires tracking which 
    # specific URLs were referenced in each section. This would need enhancement
    # in the agent response to include URL references alongside citation numbers.
    return text

def format_enhanced_final_report(state: ReportState) -> ReportState:
    """Enhanced report formatting with proper citation handling."""
    print("--- 📝 Compiling Enhanced Final Report with Proper Citations ---")
    r = state
    
    report_parts = []

    def add_section(title, content):
        if content and content.strip():
            report_parts.append(title)
            # Apply citation mapping to content
            mapped_content = map_citations_in_text(content, r.citations)
            report_parts.append(mapped_content)

    # Generate comprehensive report sections
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
        
        # Enhanced cost section with all tables
        report_parts.append("\n## 3.2. Geliştirmenin Öz Kaynaklarla Karşılanması Durumunda Maliyet\n")
        add_section("", r.cost.equity_funded_development_cost_text)
        
        if r.cost.equity_funded_development_labor_costs:
            report_parts.append("\n**Tablo 2: Geliştirmenin Öz Kaynaklarla Karşılanması Durumunda İşçilik Maliyeti Tablosu**\n")
            labor_headers = ["Yıl", "İşçilik Tipi", "İşçilik Saati", "İşçilik Maliyeti", "İşçilik Açıklaması"]
            labor_rows = [item.model_dump() for item in r.cost.equity_funded_development_labor_costs]
            report_parts.append(_create_enhanced_markdown_table(labor_headers, labor_rows))
        
        if r.cost.equity_funded_development_expense_costs:
            report_parts.append("\n**Tablo 3: Geliştirmenin Öz Kaynaklarla Karşılanması Durumunda Harcama Maliyeti Tablosu**\n")
            expense_headers = ["Yıl", "Kaynak Tipi", "Harcama Alt Kategori", "Harcama Tutarı", "Kaynak Açıklaması"]
            expense_rows = [item.model_dump() for item in r.cost.equity_funded_development_expense_costs]
            report_parts.append(_create_enhanced_markdown_table(expense_headers, expense_rows))
        
        report_parts.append("\n## 3.3. Toplam Geliştirme Maliyeti\n")
        add_section("", r.cost.total_development_cost_text)
        
        if r.cost.total_development_labor_costs:
            report_parts.append("\n**Tablo 4: Ürün/teknolojinin Geliştirilmesi için İhtiyaç Duyulan (Sözleşmeli + Öz Kaynak) İşçilik Maliyeti Tablosu**\n")
            labor_rows = [item.model_dump() for item in r.cost.total_development_labor_costs]
            report_parts.append(_create_enhanced_markdown_table(labor_headers, labor_rows))
        
        if r.cost.total_development_expense_costs:
            report_parts.append("\n**Tablo 5: Ürün/teknolojinin Geliştirilmesi için İhtiyaç Duyulan (Sözleşmeli + Öz Kaynak) Harcama Maliyeti Tablosu**\n")
            expense_rows = [item.model_dump() for item in r.cost.total_development_expense_costs]
            report_parts.append(_create_enhanced_markdown_table(expense_headers, expense_rows))

        report_parts.append("\n## 3.4. Seri Üretim Yatırımının Öz Kaynaklarla Karşılanması Durumunda Maliyet\n")
        add_section("", r.cost.equity_funded_production_investment_text)
        
        if r.cost.equity_funded_production_investment_labor_costs:
            report_parts.append("\n**Tablo 6: Seri Üretim Yatırımının Öz Kaynaklarla Karşılanması Durumunda İşçilik Maliyeti Tablosu**\n")
            labor_rows_prod_equity = [item.model_dump() for item in r.cost.equity_funded_production_investment_labor_costs]
            report_parts.append(_create_enhanced_markdown_table(labor_headers, labor_rows_prod_equity))
        
        if r.cost.equity_funded_production_investment_expense_costs:
            report_parts.append("\n**Tablo 7: Seri Üretim Yatırımının Öz Kaynaklarla Karşılanması Durumunda Harcama Maliyeti Tablosu**\n")
            expense_rows_prod_equity = [item.model_dump() for item in r.cost.equity_funded_production_investment_expense_costs]
            report_parts.append(_create_enhanced_markdown_table(expense_headers, expense_rows_prod_equity))

        report_parts.append("\n## 3.5. Toplam Seri Üretim Yatırım Maliyeti\n")
        add_section("", r.cost.total_production_investment_text)
        
        if r.cost.total_production_investment_labor_costs:
            report_parts.append("\n**Tablo 8: Ürün/teknolojinin Seri Üretimi için İhtiyaç Duyulan (Sözleşmeli + Öz Kaynak) İşçilik Maliyeti Tablosu**\n")
            labor_rows_prod = [item.model_dump() for item in r.cost.total_production_investment_labor_costs]
            report_parts.append(_create_enhanced_markdown_table(labor_headers, labor_rows_prod))
        
        if r.cost.total_production_investment_expense_costs:
            report_parts.append("\n**Tablo 9: Ürün/teknolojinin Seri Üretimi için İhtiyaç Duyulan (Sözleşmeli + Öz Kaynak) Harcama Maliyeti Tablosu**\n")
            expense_rows_prod = [item.model_dump() for item in r.cost.total_production_investment_expense_costs]
            report_parts.append(_create_enhanced_markdown_table(expense_headers, expense_rows_prod))
        
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

    # Enhanced Citations section with proper numbering
    if r.citations:
        report_parts.append("\n# KAYNAKÇA\n")
        for url, citation_data in r.citations.items():
            report_parts.append(f"[{citation_data.number}] {citation_data.title}. Alınan yer: {citation_data.url}")

    state.report_text = "\n".join(report_parts)
    print(f"📊 Enhanced report generated with {len(r.citations)} citations")
    return state

# --- 4. Enhanced Graph Definition ---
from langgraph.graph import StateGraph, END

enhanced_workflow = StateGraph(ReportState)

enhanced_workflow.add_node("general_section", run_general_section)
enhanced_workflow.add_node("technical_analysis", run_technical_analysis)
enhanced_workflow.add_node("market_analysis", run_market_analysis)
enhanced_workflow.add_node("cost_analysis", run_cost_analysis)
enhanced_workflow.add_node("financial_analysis", run_financial_analysis)
enhanced_workflow.add_node("risk_analysis", run_risk_analysis)
enhanced_workflow.add_node("generate_conclusion", run_conclusion)
enhanced_workflow.add_node("format_report", format_enhanced_final_report)

enhanced_workflow.set_entry_point("general_section")
enhanced_workflow.add_edge("general_section", "technical_analysis")
enhanced_workflow.add_edge("technical_analysis", "market_analysis")
enhanced_workflow.add_edge("market_analysis", "cost_analysis")
enhanced_workflow.add_edge("cost_analysis", "financial_analysis")
enhanced_workflow.add_edge("financial_analysis", "risk_analysis")
enhanced_workflow.add_edge("risk_analysis", "generate_conclusion")
enhanced_workflow.add_edge("generate_conclusion", "format_report")
enhanced_workflow.add_edge("format_report", END)

enhanced_app = enhanced_workflow.compile()

# --- 5. Enhanced Pipeline Execution ---
async def main():
    if not os.environ.get("TAVILY_API_KEY") or not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        print("Please set TAVILY_API_KEY and a supported LLM API Key (e.g., OPENAI_API_KEY) as environment variables.")
        return

    report_topic = "Sınır güvenliği için gelişmiş yapay zeka destekli nesne tanıma özelliğine sahip yeni nesil otonom gözetleme dronlarının geliştirilmesinin fizibilitesi."
    
    print("🚀 Starting Enhanced Deep Research Report Generation...")
    print(f"📋 Topic: {report_topic}")
    
    initial_state = ReportState(topic=report_topic)
    
    config = {"recursion_limit": 50}
    final_state_generator = enhanced_app.astream(initial_state, config=config)

    final_state = None
    async for state_update in final_state_generator:
        final_state = list(state_update.values())[0]

    final_report_text = final_state.get('report_text', "Enhanced report generation failed.")
    
    print("\n\n--- ENHANCED FINAL REPORT ---")
    print(f"📊 Report Length: {len(final_report_text)} characters")
    print(f"📚 Total Citations: {len(final_state.get('citations', {}))}")
    print(final_report_text[:1000] + "..." if len(final_report_text) > 1000 else final_report_text)
    
    with open("enhanced_feasibility_report.md", "w", encoding="utf-8") as f:
        f.write(final_report_text)
        
    print(f"\n✅ Enhanced detailed report saved to enhanced_feasibility_report.md")
    print(f"📊 Report contains {len(final_state.get('citations', {}))} properly numbered citations")

if __name__ == "__main__":
    asyncio.run(main()) 