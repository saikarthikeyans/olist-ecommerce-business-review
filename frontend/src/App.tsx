import React, { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { ExecutiveOverview } from './pages/ExecutiveOverview';
import { RevenueAnalytics } from './pages/RevenueAnalytics';
import { ProductCategories } from './pages/ProductCategories';
import { DeliverySatisfaction } from './pages/DeliverySatisfaction';
import { DataQualityPage } from './pages/DataQualityPage';
import { PipelineRunsPage } from './pages/PipelineRunsPage';
import { StagingDataExplorer } from './pages/StagingDataExplorer';
import {
  fetchDeliverySatisfaction,
  fetchHealth,
  fetchKpis,
  fetchMonthlyRevenue,
  fetchQualityAudit,
  fetchRepeatPurchases,
  fetchTopCategories,
} from './api/client';
import {
  DeliverySatisfactionRow,
  ExecutiveKpis,
  HealthStatus,
  MonthlyRevenueRow,
  PageId,
  QualityCheckAuditRow,
  RepeatPurchaseSummary,
  TopCategoryRow,
} from './types';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [loading, setLoading] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isConfigured, setIsConfigured] = useState<boolean>(true);

  // Analytics states
  const [kpis, setKpis] = useState<ExecutiveKpis | undefined>();
  const [monthlyRevenue, setMonthlyRevenue] = useState<MonthlyRevenueRow[]>([]);
  const [topCategories, setTopCategories] = useState<TopCategoryRow[]>([]);
  const [retention, setRetention] = useState<RepeatPurchaseSummary | undefined>();
  const [deliverySatisfaction, setDeliverySatisfaction] = useState<DeliverySatisfactionRow[]>([]);
  const [qualityAudit, setQualityAudit] = useState<QualityCheckAuditRow[]>([]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      // 1. Check health
      try {
        const h = await fetchHealth();
        setHealth(h);
        setIsConfigured(h.database_connected);
      } catch (e) {
        setIsConfigured(false);
      }

      // 2. Fetch KPIs
      try {
        const kpiRes = await fetchKpis();
        if (kpiRes.is_configured && kpiRes.data) {
          setKpis(kpiRes.data);
          setIsConfigured(true);
        }
      } catch (e) {
        console.warn('KPI fetch fallback');
      }

      // 3. Fetch Monthly Revenue
      try {
        const revRes = await fetchMonthlyRevenue();
        if (revRes.data) setMonthlyRevenue(revRes.data);
      } catch (e) {
        console.warn('Revenue fetch fallback');
      }

      // 4. Fetch Top Categories
      try {
        const catRes = await fetchTopCategories();
        if (catRes.data) setTopCategories(catRes.data);
      } catch (e) {
        console.warn('Category fetch fallback');
      }

      // 5. Fetch Retention
      try {
        const retRes = await fetchRepeatPurchases();
        if (retRes.data) setRetention(retRes.data);
      } catch (e) {
        console.warn('Retention fetch fallback');
      }

      // 6. Fetch Delivery vs Review
      try {
        const delRes = await fetchDeliverySatisfaction();
        if (delRes.data) setDeliverySatisfaction(delRes.data);
      } catch (e) {
        console.warn('Delivery fetch fallback');
      }

      // 7. Fetch Quality Audit
      try {
        const qualRes = await fetchQualityAudit();
        if (qualRes.data) setQualityAudit(qualRes.data);
      } catch (e) {
        console.warn('Quality fetch fallback');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const getPageTitle = (page: PageId): string => {
    switch (page) {
      case 'overview':
        return 'Executive Overview & North Star Metrics';
      case 'explorer':
        return 'Supabase Staging & Mart Interactive Explorer';
      case 'revenue':
        return 'Month-over-Month Revenue & Expansion Analytics';
      case 'categories':
        return 'Product Category Dominance by State';
      case 'delivery':
        return 'Delivery Logistics & Customer Satisfaction (CSAT)';
      case 'quality':
        return 'SQL Data Quality Verification Suite';
      case 'runs':
        return 'ELT Pipeline Runs & Architecture';
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        dbConnected={health?.database_connected ?? false}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Header
          pageTitle={getPageTitle(activePage)}
          onRefresh={loadAllData}
          loading={loading}
          dbConnected={health?.database_connected ?? false}
          datasetPresence={health?.dataset_files_present || '9/9 Files'}
        />

        <main className={activePage === 'explorer' ? 'w-full' : 'p-8 max-w-7xl w-full mx-auto'}>
          {activePage === 'overview' && (
            <ExecutiveOverview
              kpis={kpis}
              monthlyRevenue={monthlyRevenue}
              retention={retention}
              isConfigured={isConfigured}
            />
          )}

          {activePage === 'explorer' && <StagingDataExplorer />}

          {activePage === 'revenue' && (
            <RevenueAnalytics data={monthlyRevenue} isConfigured={isConfigured} />
          )}

          {activePage === 'categories' && (
            <ProductCategories data={topCategories} isConfigured={isConfigured} />
          )}

          {activePage === 'delivery' && (
            <DeliverySatisfaction data={deliverySatisfaction} isConfigured={isConfigured} />
          )}

          {activePage === 'quality' && (
            <DataQualityPage data={qualityAudit} isConfigured={isConfigured} />
          )}

          {activePage === 'runs' && <PipelineRunsPage isConfigured={isConfigured} />}
        </main>
      </div>
    </div>
  );
};

export default App;
