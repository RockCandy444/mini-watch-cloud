import "../style.css";

export const metadata = {
  title: "mini watch · Next.js 메모와 감시 대시보드",
  description: "계정을 만들고 서비스의 요청과 관찰 메모를 확인하세요.",
};

export default function RootLayout({ children }) {
  return <html lang="ko"><body>{children}</body></html>;
}
