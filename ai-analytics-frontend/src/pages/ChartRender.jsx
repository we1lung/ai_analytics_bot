import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend 
} from 'recharts';

// Красивая палитра цветов
const COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#16a34a', '#0891b2'];

export default function ChartRender({ data, type = "bar" }) {
  if (!data || data.length === 0) return <div style={{padding: 20, textAlign: 'center', opacity: 0.5}}>Нет данных для графика</div>;

  return (
    <div style={{ 
      width: '100%', 
      height: 350, 
      backgroundColor: '#fff', 
      padding: '20px', 
      borderRadius: '12px', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      marginTop: '15px',
      marginBottom: '15px'
    }}>
      <ResponsiveContainer width="100%" height="100%">
        {type === "bar" ? (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis dataKey="name" tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
            <YAxis tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)'}} />
            <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        ) : type === "line" ? (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis dataKey="name" tick={{fontSize: 12}} axisLine={false} />
            <YAxis tick={{fontSize: 12}} axisLine={false} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} dot={{ r: 6, fill: '#2563eb', strokeWidth: 2, stroke: '#fff' }} />
          </LineChart>
        ) : (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend verticalAlign="bottom" height={36}/>
          </PieChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}