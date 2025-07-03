//src/components/PartnerSelector.jsx
import {
  TruckIcon,
  PackageIcon,
  GlobeIcon,
  ArchiveIcon,
  RepeatIcon,
  BoxIcon,
} from "lucide-react";

const options = [
  { key: "brenger",   label: "Brenger",   icon: <TruckIcon className="h-5 w-5" /> },
  { key: "wuunder",   label: "Wuunder",   icon: <PackageIcon className="h-5 w-5" /> },
  { key: "libero",    label: "Libero",    icon: <GlobeIcon className="h-5 w-5" /> },
  { key: "swdevries", label: "Sw De Vries", icon: <ArchiveIcon className="h-5 w-5" /> },
  { key: "transpoksi",label: "Transpoksi", icon: <RepeatIcon className="h-5 w-5" /> },
  { key: "magic_movers", label: "Magic Movers", icon: <BoxIcon className="h-5 w-5" /> },
];

export default function PartnerSelector({ partner, setPartner }) {
  return (
    <div className="inline-flex bg-gray-100 rounded-full p-1 space-x-1">
      {options.map(opt => (
        <button
          key={opt.key}
          onClick={() => setPartner(opt.key)}
          className={`
            flex items-center space-x-2 px-4 py-2 rounded-full
            transition-colors duration-200
            ${partner === opt.key
              ? "bg-indigo-600 text-white"
              : "text-gray-700 hover:bg-white"}
          `}
        >
          {opt.icon}
          <span className="text-sm font-medium">{opt.label}</span>
        </button>
      ))}
    </div>
  );
}
