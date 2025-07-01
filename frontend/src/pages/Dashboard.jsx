//frontend/src/pages/Dashboard.jsx
import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import FileUpload from "../components/FileUpload";
import TableView from "../components/TableView";
import SummaryCard from "../components/SummaryCard";
import axios from "axios";

const Dashboard = () => {
  const { dashboardId } = useParams();
  const [data, setData] = useState([]);
  const [partner, setPartner] = useState("brenger");
  const [loading, setLoading] = useState(false);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const url = dashboardId
        ? `/api/dashboard/${dashboardId}`
        : `/api/dashboard`;
      const res = await axios.get(url);
      setData(res.data);
    } catch (error) {
      console.error("Failed to fetch dashboard data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [dashboardId]);

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Upload & Insights</h1>
      <FileUpload partner={partner} setPartner={setPartner} onUpload={fetchDashboard} />
      {loading && <div className="text-center py-10">Loading...</div>}
      {data.map((df, idx) =>
        df.Type === "summary" ? (
          <SummaryCard key={idx} {...df} />
        ) : (
          <TableView key={idx} data={df} />
        )
      )}
    </div>
  );
};

export default Dashboard;
