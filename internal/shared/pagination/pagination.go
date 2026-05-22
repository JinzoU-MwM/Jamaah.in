package pagination

type Params struct {
	Page     int `query:"page"`
	PageSize int `query:"page_size"`
	SortBy   string `query:"sort_by"`
	SortDir  string `query:"sort_dir"` // asc or desc
	Search   string `query:"search"`
}

func Default() Params {
	return Params{
		Page:     1,
		PageSize: 20,
		SortBy:   "created_at",
		SortDir:  "desc",
	}
}

func (p Params) Normalize() Params {
	if p.Page < 1 {
		p.Page = 1
	}
	if p.PageSize < 1 || p.PageSize > 100 {
		p.PageSize = 20
	}
	if p.SortBy == "" {
		p.SortBy = "created_at"
	}
	if p.SortDir != "asc" && p.SortDir != "desc" {
		p.SortDir = "desc"
	}
	return p
}

func (p Params) Offset() int {
	return (p.Page - 1) * p.PageSize
}

func (p Params) Limit() int {
	return p.PageSize
}