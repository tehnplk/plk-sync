CREATE TABLE c_bed_type_std (
  code CHAR(3) NOT NULL PRIMARY KEY COMMENT 'หลักที่ 4-5-6',
  name VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO c_bed_type_std (code, name) VALUES
-- 1 = Ward
('100', 'Ward'),
-- 2 = ICU
('201', 'ICU ทั่วไปที่ไม่ได้แยกแผนก'),
('202', 'CCU'),
('203', 'RCU'),
('204', 'SICU'),
('205', 'TICU'),
('206', 'CVT ICU'),
('207', 'PICU'),
('208', 'NICU'),
('209', 'MICU'),
('210', 'ICU อื่นๆ'),
('211', 'ICU ห้องความดันลบ'),
-- 3 = SEMI ICU
('301', 'SEMI ICU ทั่วไป'),
('302', 'SEMI ICU ห้องความดันลบ'),
('303', 'อื่นๆ'),
-- 4 = Stroke Unit
('400', 'STROKE UNIT'),
-- 5 = Burn Unit
('500', 'BURN UNIT'),
-- 6 = เตียงอื่น ๆ
('601', 'เตียง Palliative'),
('602', 'เตียง IMC'),
('603', 'เตียงเสริมจำหน่าย'),
('604', 'เตียงมูลนิธิบัญชารักษ์'),
('605', 'Observe ER'),
('606', 'เตียงห้องพิเศษ'),
('607', 'เตียง Home Ward'),
('608', 'เตียงรอคลอด'),
('609', 'CLIP เด็ก'),
-- 7 = ห้องความดันลบ
('700', 'ห้องความดันลบ');