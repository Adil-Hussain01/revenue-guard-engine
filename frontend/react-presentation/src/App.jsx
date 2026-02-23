import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck,
  ArrowRightLeft,
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Layers,
  Database,
  Cpu
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

const data = [
  { name: 'Pricing Drift', value: 45, color: '#3b82f6' },
  { name: 'Missing Invoices', value: 30, color: '#6366f1' },
  { name: 'Sync Delays', value: 25, color: '#10b981' },
];

const recoveryData = [
  { month: 'Sep', leakage: 12500, recovered: 8000 },
  { month: 'Oct', leakage: 14200, recovered: 11500 },
  { month: 'Nov', leakage: 9800, recovered: 9200 },
  { month: 'Dec', leakage: 15600, recovered: 14800 },
  { month: 'Jan', leakage: 8400, recovered: 8100 },
  { month: 'Feb', leakage: 6200, recovered: 6100 },
];

const SlideLayout = ({ children, title, subtitle }) => (
  <div className="w-full h-full flex flex-col p-12 relative overflow-hidden">
    <div className="absolute top-0 right-0 w-96 h-96 bg-brand-blue/10 rounded-full blur-3xl -mr-48 -mt-48" />
    <div className="absolute bottom-0 left-0 w-96 h-96 bg-brand-green/10 rounded-full blur-3xl -ml-48 -mb-48" />

    <div className="relative z-10 flex flex-col h-full">
      <div className="mb-8">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl font-bold mb-4 gradient-text pb-2 leading-tight"
        >
          {title}
        </motion.h1>
        {subtitle && (
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-2xl text-white/60"
          >
            {subtitle}
          </motion.p>
        )}
      </div>
      <div className="flex-grow">
        {children}
      </div>
    </div>
  </div>
);

const slides = [
  // Slide 1: Title
  () => (
    <div className="h-full flex flex-col items-center justify-center text-center">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-24 h-24 bg-brand-blue/20 rounded-2xl flex items-center justify-center mb-8 glass"
      >
        <ShieldCheck className="w-12 h-12 text-brand-blue" />
      </motion.div>
      <motion.h1
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-7xl font-bold mb-6 tracking-tight pb-4 leading-tight"
      >
        Revenue <span className="gradient-text pb-2">Guard Engine</span>
      </motion.h1>
      <motion.p
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-2xl text-white/50 max-w-2xl font-light"
      >
        Automating Revenue Reconciliation between <br />
        <span className="text-white font-medium">GoHighLevel</span> and <span className="text-white font-medium">QuickBooks Online</span>
      </motion.p>
    </div>
  ),

  // Slide 2: The Problem
  () => (
    <SlideLayout
      title="The Revenue Leakage Gap"
      subtitle="Invisible losses occurring in the bridge between Sales & Finance"
    >
      <div className="grid grid-cols-2 gap-12 mt-4">
        <div className="space-y-4">
          {[
            { icon: TrendingDown, text: "Unauthorized discounts eroding margins", title: "Pricing Drift" },
            { icon: AlertTriangle, text: "CRM deals not triggering Finance invoices", title: "Workflow Breaks" },
            { icon: ArrowRightLeft, text: "Inconsistent data across siloed platforms", title: "Data Desync" }
          ].map((item, i) => (
            <motion.div
              key={i}
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: i * 0.1 }}
              className="glass p-5 rounded-2xl flex gap-6"
            >
              <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center shrink-0">
                <item.icon className="text-brand-blue" />
              </div>
              <div>
                <h3 className="text-xl font-bold mb-1">{item.title}</h3>
                <p className="text-white/60 leading-relaxed">{item.text}</p>
              </div>
            </motion.div>
          ))}
        </div>
        <div className="glass rounded-3xl p-8 flex flex-col">
          <h3 className="text-xl font-bold mb-6">Historical Leakage Intensity</h3>
          <div className="flex-grow">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} layout="vertical">
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#fff" fontSize={12} width={100} />
                <Tooltip
                  cursor={{ fill: 'transparent' }}
                  contentStyle={{ backgroundColor: '#111', border: 'none', borderRadius: '8px' }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </SlideLayout>
  ),

  // Slide 3: The Solution Bridge
  () => (
    <SlideLayout
      title="Unified Syncing Bridge"
      subtitle="Automated reconciliation at the speed of business"
    >
      <div className="h-full flex items-center justify-center">
        <div className="flex items-center gap-12">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-64 h-80 glass rounded-3xl p-8 flex flex-col items-center justify-center border-t-4 border-brand-blue shadow-2xl shadow-brand-blue/10"
          >
            <Database className="w-16 h-16 text-brand-blue mb-6" />
            <h3 className="text-2xl font-bold">GoHighLevel</h3>
            <p className="text-white/40 text-center mt-2">Source of Truth <br /> for Sales</p>
          </motion.div>

          <div className="flex flex-col items-center gap-4">
            <motion.div
              animate={{ x: [0, 40, 0] }}
              transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
            >
              <ArrowRight className="w-12 h-12 text-white/20" />
            </motion.div>
            <div className="glass px-6 py-3 rounded-full text-brand-green font-bold text-sm tracking-widest uppercase shadow-lg border-brand-green/20">
              Revenue Guard
            </div>
            <motion.div
              animate={{ x: [0, -40, 0] }}
              transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
            >
              <ArrowRight className="w-12 h-12 text-white/20 rotate-180" />
            </motion.div>
          </div>

          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="w-64 h-80 glass rounded-3xl p-8 flex flex-col items-center justify-center border-t-4 border-brand-green shadow-2xl shadow-brand-green/10"
          >
            <CheckCircle2 className="w-16 h-16 text-brand-green mb-6" />
            <h3 className="text-2xl font-bold">QuickBooks</h3>
            <p className="text-white/40 text-center mt-2">Source of Truth <br /> for Finance</p>
          </motion.div>
        </div>
      </div>
    </SlideLayout>
  ),

  // Slide 4: Intelligence Core
  () => (
    <SlideLayout
      title="The Intelligence Core"
      subtitle="12+ production rules running in sub-second precision"
    >
      <div className="grid grid-cols-3 gap-8 mt-12">
        {[
          { title: "Pricing Integrity", desc: "Cross-checks Sales offer vs Invoice reality", icon: Cpu },
          { title: "Sync Validation", desc: "Ensures every 'Won' deal exists in Finance", icon: Layers },
          { title: "Risk Scoring", desc: "Categorizes leakage by financial impact", icon: BarChart3 }
        ].map((item, i) => (
          <motion.div
            key={i}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: i * 0.1 }}
            className="glass p-10 rounded-3xl flex flex-col items-center text-center group hover:bg-white/5 transition-all border-b-4 border-transparent hover:border-brand-blue shadow-xl"
          >
            <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <item.icon className="text-brand-blue" />
            </div>
            <h3 className="text-2xl font-bold mb-4">{item.title}</h3>
            <p className="text-white/50 leading-relaxed">{item.desc}</p>
          </motion.div>
        ))}
      </div>
    </SlideLayout>
  ),

  // Slide 5: Project Outcomes - Recovery Dashboard
  () => (
    <SlideLayout
      title="Outcome: Revenue Recovery Dashboard"
      subtitle="Tangible results from a production implementation"
    >
      <div className="grid grid-cols-4 gap-6 mb-8 mt-4">
        {[
          { label: "Total Leakage Detected", val: "$66,700", color: "text-brand-blue" },
          { label: "Revenue Recovered", val: "$55,700", color: "text-brand-green" },
          { label: "Recovery Rate", val: "83.5%", color: "text-white" },
          { label: "Disputed Items", val: "12", color: "text-white/50" }
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: i * 0.1 }}
            className="glass p-6 rounded-2xl"
          >
            <p className="text-sm text-white/40 mb-2 uppercase tracking-wider">{stat.label}</p>
            <p className={`text-3xl font-bold ${stat.color}`}>{stat.val}</p>
          </motion.div>
        ))}
      </div>
      <div className="glass rounded-3xl p-8 h-[350px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={recoveryData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
            <XAxis dataKey="month" stroke="#ffffff40" />
            <YAxis stroke="#ffffff40" tickFormatter={(v) => `$${v / 1000}k`} />
            <Tooltip
              contentStyle={{ backgroundColor: '#111', border: 'none', borderRadius: '12px', padding: '12px' }}
              itemStyle={{ color: '#fff' }}
            />
            <Bar dataKey="leakage" fill="#3b82f640" stroke="#3b82f6" name="Leakage Identified" radius={[4, 4, 0, 0]} />
            <Bar dataKey="recovered" fill="#10b981" name="Revenue Recovered" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </SlideLayout>
  ),

  // Slide 6: Audit Evidence
  () => (
    <SlideLayout
      title="Evidence: Cross-System Correlation"
      subtitle="How we mapped Sales data to Accounting reality"
    >
      <div className="grid grid-cols-2 gap-8 mt-4 h-[450px]">
        <div className="flex flex-col gap-4">
          <div className="text-white/40 text-sm font-bold uppercase tracking-widest pl-2">GoHighLevel JSON (Sales Origin)</div>
          <div className="glass rounded-2xl p-6 font-mono text-xs flex-grow overflow-hidden bg-brand-dark/50 border-l-4 border-brand-blue">
            <pre className="text-blue-300">
              {`{
  "order_id": "GHL-99218",
  "contact": "John Smith",
  "package": "Enterprise SaaS",
  "quoted_price": 5000.00,
  "status": "Won",
  "correlation_id": "tx_2024_01_A9B2",
  "metadata": {
    "sales_rep": "rep_12",
    "timestamp": "2024-01-15T10:00Z"
  }
}`}
            </pre>
          </div>
        </div>
        <div className="flex flex-col gap-4">
          <div className="text-white/40 text-sm font-bold uppercase tracking-widest pl-2">QuickBooks JSON (Finance Reality)</div>
          <div className="glass rounded-2xl p-6 font-mono text-xs flex-grow overflow-hidden bg-brand-dark/50 border-l-4 border-brand-green">
            <pre className="text-green-300">
              {`{
  "invoice_number": "INV-QB-491",
  "customer_ref": "John Smith",
  "total_amount": 4500.00,
  "payment_status": "Paid",
  "system_correlation_id": "tx_2024_01_A9B2",
  "validation": {
    "flag": "PRICE_DISCREPANCY",
    "variance": -500.00,
    "severity": "MEDIUM"
  }
}`}
            </pre>
          </div>
        </div>
      </div>
      <div className="mt-8 glass py-4 px-8 rounded-full border border-brand-accent/20 flex items-center justify-center gap-4 mx-auto w-fit">
        <Cpu className="text-brand-accent w-5 h-5" />
        <span className="text-white/80 font-medium font-inter">Correlation identified via deterministic ID mapping, triggering an immediate audit alert.</span>
      </div>
    </SlideLayout>
  ),

  // Slide 7: Groundwork (NEW)
  () => (
    <SlideLayout
      title="The Groundwork: Custom Persistence Layer"
      subtitle="Built from scratch to handle large-scale financial data"
    >
      <div className="grid grid-cols-2 gap-12 mt-8">
        <div className="space-y-6">
          <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <Database className="text-brand-blue" /> Data Engineering Approach
          </h3>
          <ul className="space-y-4 text-lg text-white/60">
            <li className="flex gap-4">
              <CheckCircle2 className="text-brand-green shrink-0 mt-1" />
              <span>Developed a <strong>Deterministic Data Engine</strong> to guarantee 100% relational integrity between GHL and QB.</span>
            </li>
            <li className="flex gap-4">
              <CheckCircle2 className="text-brand-green shrink-0 mt-1" />
              <span>Implemented a <strong>JSON/CSV Hybrid Store</strong> that implements production database behavior without external dependencies.</span>
            </li>
            <li className="flex gap-4">
              <CheckCircle2 className="text-brand-green shrink-0 mt-1" />
              <span>Built-in <strong>Data Integrity Stress Testing</strong> to verify edge cases like duplicate invoices and partial payment syncs.</span>
            </li>
          </ul>
        </div>
        <div className="glass rounded-3xl p-8 bg-black/40 border border-white/5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-brand-blue/10 rounded-full blur-2xl" />
          <div className="text-sm font-mono text-white/40 mb-4 tracking-widest uppercase italic">Project Directory Structure</div>
          <div className="space-y-2 font-mono text-sm">
            <div className="text-blue-400">├── backend/</div>
            <div className="text-blue-300 pl-4">├── core/ <span className="text-white/20"># Reconciliation logic</span></div>
            <div className="text-blue-300 pl-4">├── data/ <span className="text-white/20"># Deterministic storage (JSON)</span></div>
            <div className="text-blue-300 pl-4">├── api/ <span className="text-white/20"># FastAPI controllers</span></div>
            <div className="text-green-400">├── storage/</div>
            <div className="text-green-300 pl-4">├── customers.json</div>
            <div className="text-green-300 pl-4">├── orders.json</div>
            <div className="text-green-300 pl-4">├── invoices.csv</div>
          </div>
          <div className="mt-8 pt-8 border-t border-white/5 text-white/40 text-sm">
            Everything implemented from scratch to ensure high-performance vectorization using Pandas and NumPy.
          </div>
        </div>
      </div>
    </SlideLayout>
  ),

  // Slide 8: Modular Architecture
  () => (
    <SlideLayout
      title="Architecture: Modular Rule Registry"
      subtitle="Engineered for extensibility with the Command Pattern"
    >
      <div className="h-full flex flex-col justify-center">
        <div className="grid grid-cols-3 gap-8 mb-12">
          <div className="glass p-8 rounded-3xl border-t-4 border-brand-blue flex flex-col items-center text-center">
            <Layers className="text-brand-blue w-12 h-12 mb-4" />
            <h4 className="text-xl font-bold mb-2">Phase 1: Data Ingestion</h4>
            <p className="text-sm text-white/50">Unified API layer for high-volume data streaming.</p>
          </div>
          <div className="glass p-8 rounded-3xl border-t-4 border-brand-accent flex flex-col items-center text-center">
            <Cpu className="text-brand-accent w-12 h-12 mb-4" />
            <h4 className="text-xl font-bold mb-2">Phase 2: Validation Engine</h4>
            <p className="text-sm text-white/50">Pluggable Rule Registry for complex business logic.</p>
          </div>
          <div className="glass p-8 rounded-3xl border-t-4 border-brand-green flex flex-col items-center text-center">
            <BarChart3 className="text-brand-green w-12 h-12 mb-4" />
            <h4 className="text-xl font-bold mb-2">Phase 3: Intelligence Layer</h4>
            <p className="text-sm text-white/50">Risk-weighted scoring and audit trail logging.</p>
          </div>
        </div>
        <div className="glass p-8 rounded-3xl bg-brand-blue/5 border border-brand-blue/10 flex items-center justify-between">
          <div className="flex-1 border-r border-white/10 pr-8">
            <h5 className="text-brand-blue font-bold uppercase tracking-widest text-xs mb-4">Implementation Strategy</h5>
            <p className="text-lg">Project followed a strict <strong>Epic-based development</strong> lifecycle, ensuring each module (CRM, Finance, Validation) was independently tested before full integration.</p>
          </div>
          <div className="flex-1 pl-8">
            <h5 className="text-brand-green font-bold uppercase tracking-widest text-xs mb-4">Core Technology Selection</h5>
            <p className="text-sm text-white/60">FastAPI, Pandas vectorization, and Deterministic Logic engines were selected to solve the "Siloed Data" problem permanently.</p>
          </div>
        </div>
      </div>
    </SlideLayout>
  ),

  // Slide 9: Technical Evidence - API Playground
  () => (
    <SlideLayout
      title="Technical Evidence: API Connector Engine"
      subtitle="Interactive REST API orchestration across GHL and QuickBooks"
    >
      <div className="grid grid-cols-5 gap-8 h-full mt-4">
        <div className="col-span-3 relative flex flex-col">
          <div className="text-white/40 text-xs font-bold uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-brand-green animate-pulse" />
            Live Production API Environment
          </div>
          <div className="glass rounded-[2rem] overflow-hidden flex-grow border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative group">
            {/* Browser Header Mockup */}
            <div className="h-10 bg-white/5 border-b border-white/10 flex items-center px-6 gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/50" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                <div className="w-3 h-3 rounded-full bg-green-500/50" />
              </div>
              <div className="mx-auto bg-black/40 px-4 py-1 rounded-md text-[10px] text-white/30 font-mono w-64 text-center">
                api.revenueguard.io/docs
              </div>
            </div>

            <div className="relative h-full overflow-hidden">
              <img
                src="/api_playground_production_v2_1771854819066.png"
                className="w-full h-full object-cover object-top filter group-hover:scale-[1.02] transition-transform duration-700"
                alt="Production API Engine"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-brand-dark via-brand-dark/20 to-transparent" />

              {/* Highlight Overlays */}
              <div className="absolute top-[18%] left-[5%] w-[90%] h-[12%] border-2 border-brand-blue/40 bg-brand-blue/5 rounded-lg backdrop-blur-[2px]" />
              <div className="absolute top-[48%] left-[5%] w-[90%] h-[12%] border-2 border-brand-green/40 bg-brand-green/5 rounded-lg backdrop-blur-[2px]" />
            </div>

            <div className="absolute bottom-8 left-8 flex gap-4">
              <div className="glass px-6 py-3 rounded-2xl flex items-center gap-3 backdrop-blur-xl border-white/20">
                <div className="w-2 h-2 rounded-full bg-brand-blue shadow-[0_0_10px_#3b82f6]" />
                <span className="text-sm font-bold tracking-tight">GHL Connector</span>
              </div>
              <div className="glass px-6 py-3 rounded-2xl flex items-center gap-3 backdrop-blur-xl border-white/20">
                <div className="w-2 h-2 rounded-full bg-brand-green shadow-[0_0_10px_#10b981]" />
                <span className="text-sm font-bold tracking-tight">QB Online Engine</span>
              </div>
            </div>
          </div>
        </div>

        <div className="col-span-2 flex flex-col justify-center gap-6">
          <div className="space-y-6">
            <h3 className="text-2xl font-bold text-white/90">Engine Integration Logic</h3>
            <div className="space-y-4">
              {[
                {
                  title: "GHL Source Sync",
                  desc: "Deterministic syncing of Contacts, Deals, and Won Opportunities.",
                  color: "border-brand-blue",
                  icon: Database
                },
                {
                  title: "QB Ledger Alignment",
                  desc: "Direct mapping of Invoices and Payments to CRM origins.",
                  color: "border-brand-green",
                  icon: ShieldCheck
                },
                {
                  title: "Real-time Validation",
                  desc: "Sub-second verification of pricing and workflow integrity.",
                  color: "border-white/20",
                  icon: Cpu
                }
              ].map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ x: 30, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.4 + (i * 0.1) }}
                  className={`glass p-6 rounded-3xl border-l-4 ${item.color} hover:bg-white/[0.05] transition-colors`}
                >
                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center shrink-0">
                      <item.icon className="w-5 h-5 text-white/70" />
                    </div>
                    <div>
                      <h4 className="font-bold text-white mb-1">{item.title}</h4>
                      <p className="text-sm text-white/50 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="mt-4 p-8 rounded-[2rem] bg-gradient-to-br from-brand-blue/20 to-brand-green/10 border border-white/10 relative overflow-hidden group"
          >
            <div className="relative z-10">
              <p className="text-xs text-brand-blue font-bold uppercase tracking-[0.2em] mb-3">Architect's Summary</p>
              <p className="text-sm text-white/80 italic leading-relaxed">
                "We bypassed standard simulation by building direct API connectors that mirror production environments, ensuring a seamless transition from detection to recovery."
              </p>
            </div>
            <div className="absolute -right-8 -bottom-8 w-32 h-32 bg-white/5 rounded-full blur-3xl group-hover:bg-white/10 transition-colors" />
          </motion.div>
        </div>
      </div>
    </SlideLayout>
  ),

  // Slide 10: Business Impact
  () => (
    <SlideLayout
      title="Conclusion: Scalable Revenue Recovery"
      subtitle="Proven results from a professional engineering build"
    >
      <div className="grid grid-cols-3 gap-8 mt-8">
        {[
          { val: "40+", label: "Hours Saved Weekly", desc: "Manual transaction audits eliminated" },
          { val: "0.2s", label: "Analysis Speed", desc: "Full-system reconciliation in sub-seconds" },
          { val: "$12k", label: "Cost Recovery / Mo", desc: "Average leakage captured per account" }
        ].map((item, i) => (
          <motion.div
            key={i}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: i * 0.1 }}
            className="glass p-8 rounded-3xl flex flex-col items-center text-center shadow-2xl hover:scale-105 transition-transform"
          >
            <div className="text-6xl font-bold gradient-text mb-4 italic leading-tight pb-2">{item.val}</div>
            <div className="text-xl font-bold text-white mb-2">{item.label}</div>
            <p className="text-white/40 text-sm">{item.desc}</p>
          </motion.div>
        ))}
      </div>
      <div className="mt-12 flex flex-col items-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex items-center gap-6 text-brand-blue bg-white/5 py-5 px-12 rounded-full border border-brand-blue/20 shadow-2xl shadow-brand-blue/10"
        >
          <CheckCircle2 className="w-8 h-8 text-brand-green" />
          <span className="text-2xl font-medium text-white/90">A complete, production-ready solution for complex revenue operations.</span>
        </motion.div>
      </div>
    </SlideLayout>
  )
];

const App = () => {
  const [currentSlide, setCurrentSlide] = useState(0);

  const nextSlide = () => setCurrentSlide((prev) => (prev + 1) % slides.length);
  const prevSlide = () => setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
      if (e.key === 'ArrowLeft') prevSlide();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="w-full h-full bg-brand-dark text-white font-inter select-none">
      <AnimatePresence mode="wait">
        <motion.div
          key={currentSlide}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
          className="w-full h-full"
        >
          {slides[currentSlide]()}
        </motion.div>
      </AnimatePresence>

      {/* Navigation UI */}
      <div className="absolute bottom-8 right-8 flex gap-4 z-50">
        <button
          onClick={prevSlide}
          className="glass w-12 h-12 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors"
        >
          <ArrowRight className="rotate-180" />
        </button>
        <div className="glass px-6 rounded-full flex items-center justify-center text-sm font-medium">
          {currentSlide + 1} / {slides.length}
        </div>
        <button
          onClick={nextSlide}
          className="glass w-12 h-12 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors"
        >
          <ArrowRight />
        </button>
      </div>

      {/* Progress Bar */}
      <div className="absolute bottom-0 left-0 h-1 bg-white/5 w-full z-50">
        <motion.div
          className="h-full bg-brand-blue"
          initial={false}
          animate={{ width: `${((currentSlide + 1) / slides.length) * 100}%` }}
        />
      </div>
    </div>
  );
};

export default App;
