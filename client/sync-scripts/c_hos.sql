CREATE TABLE IF NOT EXISTS c_hos (
    hoscode  VARCHAR(5)  NOT NULL PRIMARY KEY,
    hosname  VARCHAR(255) NOT NULL,
    hostype  VARCHAR(50),
    hossize  VARCHAR(50),
    beds     INT
);

INSERT INTO c_hos (hoscode, hosname, hostype, hossize, beds) VALUES
    ('10676', 'โรงพยาบาลพุทธชินราช', NULL, NULL, NULL),
    ('11256', 'โรงพยาบาลวังทอง', NULL, NULL, NULL),
    ('11252', 'โรงพยาบาลบางระกำ', NULL, NULL, NULL),
    ('11455', 'โรงพยาบาลสมเด็จพระยุพราชนครไทย', NULL, NULL, NULL),
    ('11251', 'โรงพยาบาลชาติตระการ', NULL, NULL, NULL),
    ('11253', 'โรงพยาบาลบางกระทุ่ม', NULL, NULL, NULL),
    ('11254', 'โรงพยาบาลพรหมพิราม', NULL, NULL, NULL),
    ('11255', 'โรงพยาบาลวัดโบสถ์', NULL, NULL, NULL),
    ('11257', 'โรงพยาบาลเนินมะปราง', NULL, NULL, NULL);
