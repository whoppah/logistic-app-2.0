// src/components/DeltaChart.jsx
import { PieChart, Pie, Cell, Tooltip } from 'recharts';

const COLORS = ['#00C49F', '#FF8042'];

const DeltaChart = ({ delta_ok, delta_sum }) => {
  const data = [
    { name: 'OK', value: delta_ok },
    { name: 'Delta', value: delta_sum - delta_ok },
  ];

  return (
    <PieChart width={240} height={240}>
      <Pie data={data} dataKey="value" outerRadius={80} label>
        {data.map((entry, i) => (
          <Cell key={i} fill={COLORS[i]} />
        ))}
      </Pie>
      <Tooltip />
    </PieChart>
  );
};

export default DeltaChart;
